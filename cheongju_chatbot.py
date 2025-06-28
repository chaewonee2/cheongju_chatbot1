import streamlit as st
from openai import OpenAI
import pandas as pd

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
data = pd.read_csv("/mnt/data/cj_data_final.csv", encoding="cp949").drop_duplicates()

# 초기 시스템 메시지
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": """
너는 청주 문화유산을 감성적으로 소개하는 관광 가이드 챗봇이야.

[설명 순서]
1. 청주의 오늘 날씨와 여행 팁을 안내해줘 ☀️☔
2. 사용자가 입력한 각 관광지를 아래 순서로 소개해줘:
   • 관광지 이름 강조 + 이모지 사용 (예: 🏛️ 정북동 토성)
   • 역사, 의미, 특징, 자연 분위기, 여행 팁 포함
   • 문단마다 줄바꿈, 감성적 표현, 여행자 입장에서 말해줘
3. 해당 관광지 주변의 카페는 시스템(CSV)을 기반으로 소개해줘.
   - 카페 이름, 평점, 리뷰 요약을 예쁘게 풀어서 보여줘 ☕
4. 만약 CSV에 없는 관광지면 GPT가 직접 설명해도 괜찮아!
"""
        }
    ]

st.title("청주 문화 챗봇 ✨")

# 이전 메시지 표시
for msg in st.session_state.messages[1:]:
    if msg["role"] == "user":
        st.markdown(f"<div style='text-align: right; background-color: #dcf8c6; border-radius: 10px; padding: 8px; margin: 5px 0;'>{msg['content']}</div>", unsafe_allow_html=True)
    elif msg["role"] == "assistant":
        st.markdown(f"<div style='text-align: left; background-color: #ffffff; border-radius: 10px; padding: 8px; margin: 5px 0;'>{msg['content']}</div>", unsafe_allow_html=True)

st.divider()

# 사용자 입력창
user_input = st.text_input("궁금한 청주의 관광지를 입력해보세요! (예: 청남대, 문의문화재단지)")

# 카페 포맷 함수
def format_cafes(cafes_df):
    if cafes_df.empty:
        return "❌ 주변 카페 정보가 없어요. 대신 가까운 곳을 찾아보는 건 어때요?"

    result = ["☕ **주변 추천 카페 TOP 3**\n"]
    for i, row in enumerate(cafes_df.itertuples(), 1):
        stars = f"⭐ {row.c_value}"
        cafe_block = f"{i}️⃣ **{row.c_name}** ({stars})  \n“{row.c_review}”"
        result.append(cafe_block)

    return "\n\n".join(result)

# 버튼 클릭 시 실행
if st.button("보내기") and user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.spinner("청주의 아름다움을 정리 중이에요..."):
        places = [p.strip() for p in user_input.split(',')]
        response_blocks = []

        # 날씨 소개
        weather_intro = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "너는 청주 문화관광 가이드야. 오늘 청주의 날씨를 여행자에게 소개해줘. 옷차림, 우산 팁도 함께."}
            ]
        ).choices[0].message.content
        response_blocks.append(f"🌤️ {weather_intro}")

        # 관광지별 설명 + 카페 매칭
        for place in places:
            matched = data[data['t_name'].str.contains(place, na=False)]

            # GPT에게 관광지 설명 생성 요청
            gpt_place_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "너는 청주 문화유산을 감성적으로 소개하는 관광 가이드야."},
                    {"role": "user", "content": f"{place}에 대해 감성적이고 역사적인 설명을 해줘. 이모지와 줄바꿈도 적절히 써줘."}
                ]
            ).choices[0].message.content

            # 카페 정보
            if not matched.empty:
                cafes = matched[['c_name', 'c_value', 'c_review']].drop_duplicates().head(3)
                cafe_info = format_cafes(cafes)
            else:
                cafe_info = "\n\n❗ CSV에서 해당 관광지를 찾을 수 없어. 근처 카페는 GPT가 임의로 추천할 수 있어요!"

            # 조합
            full_block = f"---\n\n{gpt_place_response}\n\n{cafe_info}"
            response_blocks.append(full_block)

        final_response = "\n\n".join(response_blocks)
        st.session_state.messages.append({"role": "assistant", "content": final_response})
