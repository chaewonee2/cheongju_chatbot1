import streamlit as st
import pandas as pd
import requests
from openai import OpenAI

# GPT & 날씨 API Key
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# CSV 데이터 로드
data = pd.read_csv("cj_data_final.csv", encoding="cp949").drop_duplicates()

# 날씨 API 함수
def get_weather_summary():
    try:
        API_KEY = st.secrets["weather"]["WEATHER_API_KEY"]
        url = f"http://api.openweathermap.org/data/2.5/weather?q=Cheongju,KR&appid={API_KEY}&units=metric&lang=kr"
        res = requests.get(url).json()

        if res.get("cod") != 200:
            return "🌤️ 현재 청주의 날씨 정보를 불러오지 못했어요."

        temp = res["main"]["temp"]
        weather = res["weather"][0]["description"]

        if temp < 10:
            tip = "❄️ 꽤 쌀쌀해요. 따뜻한 옷 꼭 챙기세요!"
        elif temp < 20:
            tip = "🧥 선선한 날씨네요. 가벼운 겉옷 추천드려요."
        elif temp < 28:
            tip = "☀️ 따뜻하고 활동하기 좋아요!"
        else:
            tip = "🌞 더운 날씨예요. 수분 섭취 꼭 하세요!"

        return f"🌤️ 지금 청주의 날씨는 **{weather}**, 기온은 **{temp:.1f}°C**입니다.\\n{tip}"
    except Exception as e:
        return f\"🌤️ 날씨 정보를 가져오는 중 문제가 발생했어요: {e}\"

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

# 초기 세션 설정
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "너는 청주 문화유산을 소개하는 감성 관광 가이드 챗봇이야."}
    ]

st.title("청주 문화 챗봇 ✨")

# 이전 메시지 출력
for msg in st.session_state.messages[1:]:
    if msg["role"] == "user":
        st.markdown(f"<div style='text-align: right; background-color: #dcf8c6; border-radius: 10px; padding: 8px; margin: 5px 0;'>{msg['content']}</div>", unsafe_allow_html=True)
    elif msg["role"] == "assistant":
        st.markdown(f"<div style='text-align: left; background-color: #ffffff; border-radius: 10px; padding: 8px; margin: 5px 0;'>{msg['content']}</div>", unsafe_allow_html=True)

st.divider()

user_input = st.text_input("궁금한 청주의 관광지를 입력해보세요! (예: 청남대, 문의문화재단지)")

if st.button("보내기") and user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.spinner("청주의 아름다움을 정리 중이에요..."):
        places = [p.strip() for p in user_input.split(',')]
        response_blocks = []

        # ✅ 날씨 요약 추가
        weather_intro = get_weather_summary("Cheongju")
        response_blocks.append(weather_intro)

        # ✅ 관광지별 설명 + 카페 정보
        for place in places:
            matched = data[data['t_name'].str.contains(place, na=False)]

            # GPT에게 관광지 설명 요청
            gpt_place_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "너는 청주 문화유산을 감성적으로 소개하는 관광 가이드야."},
                    {"role": "user", "content": f"{place}에 대해 감성적이고 역사적인 설명을 해줘. 이모지와 줄바꿈도 적절히 써줘."}
                ]
            ).choices[0].message.content

            if not matched.empty:
                cafes = matched[['c_name', 'c_value', 'c_review']].drop_duplicates().head(3)
                cafe_info = format_cafes(cafes)
            else:
                cafe_info = "\n\n❗ CSV에서 해당 관광지를 찾을 수 없어. 근처 카페는 GPT가 임의로 추천할 수 있어요!"

            full_block = f"---\n\n{gpt_place_response}\n\n{cafe_info}"
            response_blocks.append(full_block)

        final_response = "\n\n".join(response_blocks)
        st.session_state.messages.append({"role": "assistant", "content": final_response})
