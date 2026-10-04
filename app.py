import streamlit as st
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr
import difflib
import pandas as pd
from datetime import datetime

# 設定網頁標題與寬度
st.set_page_config(page_title="三年級語文小達人 - 繞口令大挑戰", page_icon="🎙️", layout="centered")

# 模擬資料庫
if "records" not in st.session_state:
    st.session_state.records = []

# 根據課本內容自訂的三年級專屬繞口令題庫
TONGUE_TWISTERS = {
    "🌱 第1關：小綠與小力 (ㄌ與ㄏ發音挑戰)": "小綠送紅花，小力送黃花，小綠想拿紅花換小力的黃花，小力想把黃花換小綠的紅花。",
    "✈️ 第2關：灰雞上飛機 (ㄐ、ㄑ、ㄈ氣流挑戰)": "抱著灰雞上飛機，飛機起飛，灰雞要飛。",
    "🦁 第3關：柿子與獅子 (平翹舌 ㄕ 與 ㄙ 大對決)": "是柿子不是獅子，不是石子是柿子。",
    "🐒 第4關：桃枝落桃子 (捲舌與流暢度大考驗)": "風吹桃枝落桃子，桃枝落桃撞猴子。"
}

def evaluate_grade3(target, spoken):
    """專為三年級設計的評分與引導回饋"""
    if not spoken:
        return 0, "哎呀！沒有聽到你的聲音，是不是麥克風沒打開呢？再試一次吧！"
    
    # 計算字串相似度
    similarity = difflib.SequenceMatcher(None, target, spoken).ratio()
    score = round(similarity * 100, 1)
    
    # 三年級風格的鼓勵回饋
    if score == 100:
        feedback = "太厲害了！完全零失誤，咬字超級清晰，老師要給你一個大大的👍！"
    elif score >= 80:
        feedback = "表現非常棒！只有一兩個字不小心滑掉了，再挑戰一次絕對能滿分！🌟"
    elif score >= 60:
        feedback = "很不錯喔！繞口令本來就不簡單，試著放慢速度把每個字唸清楚看看！💪"
    else:
        feedback = "沒關係，我們慢慢來！深呼吸，先看清楚題目再唸一次，你一定可以的！🔥"
        
    return score, feedback

# --- 介面切換：學生端 vs 老師端 ---
st.sidebar.title("🧭 導覽選單")
app_mode = st.sidebar.radio("切換模式", ["🎤 三年級學生挑戰區", "📊 老師後台管理區"])

if app_mode == "🎤 三年級學生挑戰區":
    st.title("🎙️ 語文小達人：課本繞口令大挑戰")
    st.write("請輸入你的名字，選擇課本裡的挑戰關卡，對著平板勇敢唸出來吧！")
    
    # 學生基本資料
    col_n1, col_n2 = st.columns(2)
    with col_n1:
        student_class = st.text_input("🏫 班級：", placeholder="例如：三信班")
    with col_n2:
        student_name = st.text_input("👤 姓名/座號：", placeholder="例如：15號 王小明")
    
    # 選擇題目
    selected_title = st.selectbox("🎯 選擇挑戰關卡：", list(TONGUE_TWISTERS.keys()))
    target_text = TONGUE_TWISTERS[selected_title]
    
    st.info(f"**請看著螢幕唸出以下句子：**\n\n### 👉 {target_text}")
    
    st.write("---")
    st.write("👇 **點擊下方紅色按鈕開始錄音（唸完後再點一次停止）**")
    
    # iPad 專用的錄音元件
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
                
                # 評分
                score, feedback = evaluate_grade3(target_text, student_spoken)
                
                # 顯示結果
                st.subheader("📝 挑戰成績單")
                st.write(f"**你剛才唸的內容：** {student_spoken}")
                st.metric(label="得分", value=f"{score} 分")
                
                if score >= 85:
                    st.balloons()
                
                st.success(f"💡 **AI 老師回饋：** {feedback}")
                
                # 記錄儲存
                full_name_id = f"{student_class} {student_name}"
                record_entry = {
                    "時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "學生": full_name_id,
                    "挑戰關卡": selected_title,
                    "語音辨識內容": student_spoken,
                    "得分": score,
                    "評語": feedback
                }
                
                if not st.session_state.records or st.session_state.records[-1] != record_entry:
                    st.session_state.records.append(record_entry)
                    
            except sr.UnknownValueError:
                st.error("❌ 哎呀，聽不清楚你說什麼，可能是周圍有點吵，試著靠近麥克風大聲一點點！")
            except sr.RequestError as e:
                st.error(f"❌ 網路連線發生錯誤：{e}")

elif app_mode == "📊 老師後台管理區":
    st.title("📊 教師評分與全班表現後台")
    st.write("這裡可以查看三年級學生的課本繞口令挑戰歷史紀錄與平均表現。")
    
    if len(st.session_state.records) == 0:
        st.warning("目前還沒有學生上傳紀錄喔！")
    else:
        df = pd.DataFrame(st.session_state.records)
        
        st.dataframe(df, use_container_width=True)
        
        # 統計數據
        col1, col2, col3 = st.columns(3)
        col1.metric("總挑戰次數", len(df))
        col2.metric("平均分數", f"{round(df['得分'].mean(), 1)} 分")
        col3.metric("最高分數", f"{df['得分'].max()} 分")
        
        # 下載報表
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 下載全班成績報表 (CSV)",
            data=csv,
            file_name=f"grade3_textbook_tongue_twister_{datetime.now().strftime('%Y%m%d')}.csv",
            mime='text/csv',
        )