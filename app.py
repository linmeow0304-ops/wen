import streamlit as st
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr
import difflib
import pandas as pd
from datetime import datetime
import requests # 新增了負責傳送資料的套件
import json

st.set_page_config(page_title="三年級語文小達人 - 繞口令大挑戰", page_icon="🎙️", layout="centered")

# ==========================================
# ⚠️ 請將下一行的網址，換成您剛剛在 Google 複製的網址
GAS_URL = "請把你的網址貼在這裡" 
# ==========================================

TONGUE_TWISTERS = {
    "🌱 第1關：小綠與小力 (ㄌ與ㄏ發音挑戰)": "小綠送紅花，小力送黃花，小綠想拿紅花換小力的黃花，小力想把黃花換小綠的紅花。",
    "✈️ 第2關：灰雞上飛機 (ㄐ、ㄑ、ㄈ氣流挑戰)": "抱著灰雞上飛機，飛機起飛，灰雞要飛。",
    "🦁 第3關：柿子與獅子 (平翹舌 ㄕ 與 ㄙ 大對決)": "是柿子不是獅子，不是石子是柿子。",
    "🐒 第4關：桃枝落桃子 (捲舌與流暢度大考驗)": "風吹桃枝落桃子，桃枝落桃撞猴子。"
}

def evaluate_grade3(target, spoken):
    if not spoken:
        return 0, "哎呀！沒有聽到你的聲音，是不是麥克風沒打開呢？再試一次吧！"
    similarity = difflib.SequenceMatcher(None, target, spoken).ratio()
    score = round(similarity * 100, 1)
    if score == 100:
        return score, "太厲害了！完全零失誤，咬字超級清晰，老師要給你一個大大的👍！"
    elif score >= 80:
        return score, "表現非常棒！只有一兩個字不小心滑掉了，再挑戰一次絕對能滿分！🌟"
    elif score >= 60:
        return score, "很不錯喔！繞口令本來就不簡單，試著放慢速度把每個字唸清楚看看！💪"
    else:
        return score, "沒關係，我們慢慢來！深呼吸，先看清楚題目再唸一次，你一定可以的！🔥"

st.title("🎙️ 語文小達人：課本繞口令大挑戰")
st.write("請輸入你的名字，選擇課本裡的挑戰關卡，對著平板勇敢唸出來吧！")
    
col_n1, col_n2 = st.columns(2)
with col_n1:
    student_class = st.text_input("🏫 班級：", placeholder="例如：三信班")
with col_n2:
    student_name = st.text_input("👤 姓名/座號：", placeholder="例如：15號 王小明")
    
selected_title = st.selectbox("🎯 選擇挑戰關卡：", list(TONGUE_TWISTERS.keys()))
target_text = TONGUE_TWISTERS[selected_title]
    
st.info(f"**請看著螢幕唸出以下句子：**\n\n### 👉 {target_text}")
st.write("---")
st.write("👇 **點擊下方紅色按鈕開始錄音（唸完後再點一次停止）**")
    
audio = mic_recorder(start_prompt="🔴 開始錄音", stop_prompt="⏹️ 停止並送出", key='recorder_textbook')
    
if audio is not None:
    if not student_name or not student_class:
        st.warning("⚠ 請先在上方填寫你的「班級」與「姓名/座號」，才能送出成績喔！")
    else:
        st.success("🎉 錄音成功！AI 老師正在仔細聽你唸的字...")
        audio_bytes = audio['bytes']
        recognizer = sr.Recognizer()
        try:
            with open("temp_audio.wav", "wb") as f:
                f.write(audio_bytes)
            with sr.AudioFile("temp_audio.wav") as source:
                audio_data = recognizer.record(source)
                student_spoken = recognizer.recognize_google(audio_data, language="zh-TW")
                
            score, feedback = evaluate_grade3(target_text, student_spoken)
                
            st.subheader("📝 挑戰成績單")
            st.write(f"**你剛才唸的內容：** {student_spoken}")
            st.metric(label="得分", value=f"{score} 分")
            if score >= 85: st.balloons()
            st.success(f"💡 **AI 老師回饋：** {feedback}")
                
            # 將資料打包送到 Google 試算表
            record_data = {
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "student_class": student_class,
                "student_name": student_name,
                "level": selected_title,
                "spoken": student_spoken,
                "score": score,
                "feedback": feedback
            }
            
            # 傳送請求
            if GAS_URL != "https://script.google.com/a/macros/kcis.ntpc.edu.tw/s/AKfycbx0ZVDnX6EjA7Zt7mJQ1R6zCZ3xOLbuX14uCPkQhE45cVlGuMYxoVtnA2RaGNcztH_OWA/exec":
                response = requests.post(GAS_URL, json=record_data)
                if response.status_code == 200:
                    st.success("✅ 成績已自動傳送給老師！")
                else:
                    st.error("⚠️ 成績傳送失敗，請通知老師。")
            else:
                st.warning("⚠️ 老師尚未設定成績儲存庫，此次成績僅供參考。")

        except sr.UnknownValueError:
            st.error("❌ 哎呀，聽不清楚你說什麼，可能是周圍有點吵，試著靠近麥克風大聲一點點！")
        except sr.RequestError as e:
            st.error(f"❌ 網路連線發生錯誤：{e}")
