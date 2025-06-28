import streamlit as st
import pandas as pd
import requests
from openai import OpenAI

# GPT Key
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# CSV 데이터 로드
data = pd.read_csv("cj_data_final.csv", encoding="cp949").drop_duplicates()

# 카페 포맷 함수 (존댓말 + 리뷰 없으면 생략)
def format_cafes(cafes_df):
    cafes_df = cafes_df.drop_duplicates()
    n = len(cafes_df)

    if n == 0:
        return ("☕ 현재 이 관광지 주변에 등록된 카페 정보는 없습니다.  \n"
                "하지만 근처에 숨은 보석 같은 공간이 있을 수 있으니,  \n"
                "지도를 활용해 주변을 탐방해보시는 것도 좋겠습니다!")

    elif n == 1:
        row = cafes_df.iloc[0]
        review_line = f"“{row['c_review']}”\n작고 조용한 분위기에서 여유를 느끼기 좋습니다." if "없음" not in row['c_review'] else ""
        return f"""☕ **주변 추천 카페**\n
- **{row['c_name']}** (⭐ {row['c_value']})  
{review_line}"""

    else:
        result = ["☕ **주변에 이런 카페들이 있어요**\n"]
        for _, row in cafes_df.iterrows():
            if "없음" not in row['c_review']:
                result.append(f"- **{row['c_name']}** (⭐ {row['c_value']})  \n“{row['c_review']}”")
            else:
                result.append(f"- **{row['c_name']}** (⭐ {row['c_value']})")
        return "\n\n".join(result)

# 초기 세션 설정
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "당신은 청주 문화유산을 소개하는 감성적이고 공손한 말투의 관광 가이드 챗봇입니다."}
    ]

st.title("청주 문화 관광가이드✨")

# 이전 메시지 출력
for msg in st.session_state.messages[1:]:
    if msg["role"] == "user":
        st.markdown(f"<div style='text-align: right; background-color: #dcf8c6; border-radius: 10px; padding: 8px; margin: 5px 0;'>{msg['content']}</div>", unsafe_allow_html=True)
    elif msg["role"] == "assistant":
        st.markdown(f"<div style='text-align: left; background-color: #ffffff; border-radius: 10px; padding: 8px; margin: 5px 0;'>{msg['content']}</div>", unsafe_allow_html=True)

st.divider()

with st.form("chat_form"):
    user_input = st.text_input("궁금한 청주의 관광지를 입력해보세요! (예: 청주 신선주, 청주 청녕각)")
    submitted = st.form_submit_button("보내기")

if submitted and user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.spinner("청주의 아름다움을 정리 중입니다..."):
        places = [p.strip() for p in user_input.split(',')]
        response_blocks = []

        # GPT 날씨 생성 (존댓말 톤)
        weather_intro = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "당신은 청주 관광을 소개하는 감성적이고 공손한 가이드입니다."},
                {"role": "user", "content": "오늘 청주의 날씨와 여행 팁을 공손한 말투로 소개해 주세요."}
            ]
        ).choices[0].message.content
        response_blocks.append(f"\U0001F324️ {weather_intro}")

        for place in places:
            matched = data[data['t_name'].str.contains(place, na=False)]

            gpt_place_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 청주 문화유산을 소개하는 공손하고 감성적인 관광 가이드입니다."},
                    {"role": "user", "content": f"{place}에 대해 감성적이고 역사적인 설명을 해 주세요. 공손한 말투로, 이모지와 줄바꿈도 활용해 주세요."}
                ]
            ).choices[0].message.content

            if not matched.empty:
                cafes = matched[['c_name', 'c_value', 'c_review']].drop_duplicates()
                cafe_info = format_cafes(cafes)
            else:
                cafe_info = "\n\n❗ CSV에서 해당 관광지를 찾지 못했습니다. GPT가 대신 주변 장소를 소개드릴 수 있어요."

            # 관광지 리뷰 정리
            reviews = matched['t_review'].dropna().unique()
            if len(reviews) > 0:
                top_reviews = list(reviews)[:3]
                review_text = "\n".join([f"“{r}”" for r in top_reviews])
                review_block = f"\n\n💬 **방문자 리뷰 중 일부**\n{review_text}"
            else:
                review_block = ""

            full_block = f"---\n\n{gpt_place_response}{review_block}\n\n{cafe_info}"
            response_blocks.append(full_block)

        final_response = "\n\n".join(response_blocks)
        st.session_state.messages.append({"role": "assistant", "content": final_response})
