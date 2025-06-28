import streamlit as st
from openai import OpenAI
import pandas as pd

# GPT API 클라이언트 설정
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# CSV 데이터 불러오기
data = pd.read_csv("./cj_data_final.csv", encoding="cp949").drop_duplicates()

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": """
너는 청주 문화유산을 친절하고 설레는 말투로 소개하는 관광 가이드 챗봇이야.

[역할 요약]
- 사용자가 입력한 청주의 관광지를 순서대로 소개해줘.
- 설명 시작 전에는 청주의 오늘 날씨를 간단히 안내하고, 여행자에게 필요한 팁도 줘.
- 관광지마다 굵은 제목(이모지 포함) + 역사/특징/팁/감성 묘사로 구성해.
- 주변 카페는 시스템(CSV)에서 줄 테니, 이름/평점/리뷰를 감성적으로 말로 풀어서 소개해.
- 카페 정보가 없으면 네가 직접 추천해줘도 좋아.
"""
        }
    ]

st.title("청주 문화 챗봇 ✨")

# 채팅 히스토리 표시
for msg in st.session_state.messages[1:]:
    if msg["role"] == "user":
        st.markdown(f"<div style='text-align: right; background-color: #dcf8c6; border-radius: 10px; padding: 8px; margin: 5px 0;'>{msg['content']}</div>", unsafe_allow_html=True)
    elif msg["role"] == "assistant":
        st.markdown(f"<div style='text-align: left; background-color: #ffffff; border-radius: 10px; padding: 8px; margin: 5px 0;'>{msg['content']}</div>", unsafe_allow_html=True)

st.divider()

# 사용자 입력
user_input = st.text_input("궁금한 청주의 관광지를 입력해보세요! (예: 청남대, 문의문화재단지)")

if st.button("보내기") and user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.spinner("청주의 아름다움을 정리 중이에요..."):

        # 관광지 리스트 추출
        places = [p.strip() for p in user_input.split(',')]
        response_blocks = []

        # 날씨 안내는 GPT가 생성
        weather_intro = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "너는 청주 문화관광 가이드야. 오늘 청주의 날씨를 여행자에게 소개해줘. 옷차림, 우산 팁 등도 포함해줘."}
            ]
        ).choices[0].message.content
        response_blocks.append(weather_intro)

        # 각 관광지 처리
        for place in places:
            matched = data[data['t_name'].str.contains(place, na=False)]

            # 관광지 설명 요청
            gpt_place_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "너는 청주 문화유산을 감성적으로 소개하는 관광 가이드야."},
                    {"role": "user", "content": f"{place}에 대해 감성적이고 역사적인 설명을 해줘. 이모지와 줄바꿈도 적절히 써줘."}
                ]
            ).choices[0].message.content

            # 카페 정보 처리
            if not matched.empty:
                cafes = matched[['c_name', 'c_value', 'c_review']].drop_duplicates().head(3)
                cafe_lines = []
                for _, row in cafes.iterrows():
                    cafe_lines.append(f"- **{row['c_name']}** (⭐ {row['c_value']}): {row['c_review']}")
                cafe_info = "\n\n☕️ 주변 추천 카페 정보:\n" + "\n".join(cafe_lines)
            else:
                cafe_info = "\n\n(해당 관광지 주변 카페 정보가 없어, 직접 추천할 수 있어요!)"

            response_blocks.append(gpt_place_response + cafe_info)

        # 전체 응답 구성
        final_response = "\n\n---\n\n".join(response_blocks)
        st.session_state.messages.append({"role": "assistant", "content": final_response})
