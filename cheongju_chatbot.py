import streamlit as st
import pandas as pd
import requests
import re
from openai import OpenAI

# GPT Key
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# CSV 데이터 로드
data = pd.read_csv("cj_data_final.csv", encoding="cp949").drop_duplicates()

# 카페 포맷 함수 (카페별 최대 2~3개 리뷰만, 없으면 생략 또는 메시지 출력)
def format_cafes(cafes_df):
    cafes_df = cafes_df.drop_duplicates(subset=['c_name', 'c_value', 'c_review'])
    result = []

    if len(cafes_df) == 0:
        return ("☕ 현재 이 관광지 주변에 등록된 카페 정보는 없습니다.  \n"
                "하지만 근처에 숨은 보석 같은 공간이 있을 수 있으니,  \n"
                "지도를 활용해 주변을 탐방해보시는 것도 좋겠습니다!")

    elif len(cafes_df) == 1:
        row = cafes_df.iloc[0]
        if all(x not in row["c_review"] for x in ["없음", "없읍"]):
            return f"""☕ **주변 추천 카페**\n\n- **{row['c_name']}** (⭐ {row['c_value']})  \n“{row['c_review']}”"""
        else:
            return f"""☕ **주변 추천 카페**\n\n- **{row['c_name']}** (⭐ {row['c_value']})  \n리뷰가 아직 존재하지 않아요."""

    else:
        grouped = cafes_df.groupby(['c_name', 'c_value'])
        result.append("☕ **주변에 이런 카페들이 있어요**  \n")
        for (name, value), group in grouped:
            reviews = group['c_review'].dropna().unique()
            reviews = [r for r in reviews if all(x not in r for x in ["없음", "없읍"])]
            top_reviews = reviews[:3]

            if top_reviews:
                review_text = "\n".join([f"“{r}”" for r in top_reviews])
                result.append(f"- **{name}** (⭐ {value})  \n{review_text}")
            else:
                result.append(f"- **{name}** (⭐ {value})  \n리뷰가 아직 존재하지 않아요.")

        return "\n\n".join(result)

# 초기 세션 설정
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "당신은 청주 문화유산을 소개하는 감성적이고 공손한 말투의 관광 가이드 챗봇입니다."}
    ]

st.title("🏞️ 청주 문화 관광가이드 🏞️")

# 이전 메시지 출력
for msg in st.session_state.messages[1:]:
    if msg["role"] == "user":
        st.markdown(f"<div style='text-align: right; background-color: #dcf8c6; border-radius: 10px; padding: 8px; margin: 5px 0;'>{msg['content']}</div>", unsafe_allow_html=True)
    elif msg["role"] == "assistant":
        st.markdown(f"<div style='text-align: left; background-color: #ffffff; border-radius: 10px; padding: 8px; margin: 5px 0;'>{msg['content']}</div>", unsafe_allow_html=True)

st.divider()

# 입력 폼 처리
with st.form("chat_form"):
    user_input = st.text_input("지도에서 선택한 관광지들을 여기에 입력해주세요! ( 쉼표(,)로 구분해 주세요. 예: 청주 신선주, 청주 청녕각)")
    submitted = st.form_submit_button("보내기")

if submitted and user_input:
    st.session_state.messages.appe