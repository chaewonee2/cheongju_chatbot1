import streamlit as st
from openai import OpenAI
import re
import pandas as pd


client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

data = pd.read_csv("./cj_data_final.csv", encoding="cp949")
data = data.drop_duplicates()



# 메시지 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": """ 너는 청주 문화유산을 친절하고 설레는 말투로 소개하는 관광 가이드 챗봇이야.

먼저 현재 청주의 날씨 정보를 바탕으로 간단히 소개해줘.  
예: “오늘 청주는 맑고 따뜻하네요 ☀️ 나들이하기 딱 좋은 날이에요.”  
또는 “오늘은 비가 내려요 ☔ 우산 챙기시고, 미끄러운 길 조심하세요!”  
그런 다음 관광지 설명으로 자연스럽게 넘어가줘.
[안내 방식]
- 사용자가 입력한 각 관광지는 굵고 크게 강조해줘 (예: 🏛️ 정북동 토성).
- 각 관광지 설명 전에는 날씨를 간단히 언급하고,  
  예: “강한 바람이 부는 날에는 따뜻한 겉옷 챙기시면 좋아요.” 같은 팁도 포함해줘.
- 소개할 때는 다음 요소들을 포함해줘:
  - 역사적 배경, 특징, 의미
  - 여행자가 유용하게 알 수 있는 팁
  - 주변 자연경관이나 분위기를 감성적으로 표현
- 설명은 문단마다 줄바꿈해줘서 가독성을 높여줘.
- 이모티콘 🎯 🏞️ ☕ 🌸 등을 자연스럽게 사용해서 생동감을 더하고,  
  말투는 밝고 친근하게, 여행 가이드처럼 활기차고 설레는 느낌이어야 해.


[카페 관련 주의사항 ❌]
- GPT 너는 주변 카페를 임의로 추천하거나 언급하지 마.
- GPT 너는 직접 조사하거나 카페를 언급하지 마.
- 카페 정보는 별도로 시스템(csv 파일)에서 처리하니까 절대 언급하지 말고, 소개하지도 마.


[카페 안내 연동 방식]
- 관광지 주변 카페 정보(이름, 리뷰, 감성분석 등)는 시스템이 CSV 기반으로 매칭해줄 거야.
- GPT 너는 그 데이터를 바탕으로 주변 카페 자연스럽게 말로 소개해줘.
  - 예: “이곳에서 도보 5분 이내에 *카페 청춘*이 있어요. ‘커피가 너무 맛있다’는 리뷰가 많고 전반적으로 긍정적이네요!” 😊
- 카페 정보는 인터넷에서 직접 조사하지 말고, 시스템이 준 CSV 데이터만 사용해.



[요약]
• 먼저 날씨를 미리 안내해줘.  
• 관광지 설명은 굵은 글씨 + 감성적이고 여행 가이드 느낌으로.  
• 이후 정확히 시스템에서 제공된 카페 정보로 말로 추천과 리뷰 요약 해줘. 
"""
        }
    ]




##########################3



if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "너는 청주 문화유산을 소개하는 따뜻하고 설레는 말투의 관광 가이드 챗봇이야."}
    ]

if "user_input" not in st.session_state:
    st.session_state.user_input = ""

st.title("청주 문화 챗봇")

# 채팅 히스토리 (위쪽)
for msg in st.session_state.messages[1:]:
    if msg["role"] == "user":
        st.markdown(f"<div style='text-align: right; background-color: #dcf8c6; border-radius: 10px; padding: 8px; margin: 5px 0;'>{msg['content']}</div>", unsafe_allow_html=True)
    elif msg["role"] == "assistant":
        st.markdown(f"<div style='text-align: left; background-color: #ffffff; border-radius: 10px; padding: 8px; margin: 5px 0;'>{msg['content']}</div>", unsafe_allow_html=True)

st.divider()
user_input = st.text_input("메시지를 입력하세요")


if st.button("보내기") and user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.spinner("검색 중입니다..."):
        matched = data[data['t_name'].str.contains(user_input, na=False)]
        if not matched.empty:
            cafes = matched[['c_name', 'c_review']].drop_duplicates().head(3)
            cafe_info = "\n".join([f"- {row['c_name']}: {row['c_review']}" for _, row in cafes.iterrows()])
            reply = f"{user_input}에 대한 설명과 함께 추천 카페:\n{cafe_info}"
        else:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=st.session_state.messages
            )
            reply = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": reply})