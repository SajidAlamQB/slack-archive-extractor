"""
Slack Archive Extractor
Upload a slackdump sqlite file and download extracted messages as JSON or TXT.
"""

import streamlit as st
import sqlite3
import json
import tempfile
from datetime import datetime
from collections import defaultdict
from pathlib import Path

st.set_page_config(page_title="Slack Archive Extractor", page_icon="💬")

st.title("💬 Slack Archive Extractor")
st.write("Upload a slackdump `.sqlite` file to extract messages for LLM analysis.")


def format_timestamp(ts) -> str:
    if not ts:
        return ""
    try:
        if isinstance(ts, str) and '.' in ts:
            ts = float(ts)
        return datetime.fromtimestamp(float(ts)).strftime('%Y-%m-%d %H:%M:%S')
    except:
        return str(ts)


def extract_data(db_path: str):
    conn = sqlite3.connect(db_path)
    
    # Get channels
    channels = {}
    try:
        for row in conn.execute("SELECT ID, NAME FROM CHANNEL"):
            channels[row[0]] = row[1]
    except:
        pass
    
    # Get users
    users = {}
    try:
        for row in conn.execute("SELECT ID, USERNAME FROM S_USER"):
            users[row[0]] = row[1] or row[0]
    except:
        pass
    
    # Get messages
    messages = []
    try:
        for row in conn.execute("SELECT CHANNEL_ID, TS, TXT, THREAD_TS FROM MESSAGE ORDER BY TS"):
            messages.append({
                'channel_id': row[0],
                'ts': row[1],
                'text': row[2],
                'thread_ts': row[3]
            })
    except:
        pass
    
    conn.close()
    
    # Organize by channel, deduplicate
    organized = defaultdict(lambda: {"messages": {}, "threads": defaultdict(dict)})
    
    for msg in messages:
        ch_id = msg.get('channel_id', 'unknown')
        ch_name = channels.get(ch_id, ch_id)
        text = msg.get('text') or ''
        
        # Replace user mentions
        for user_id, username in users.items():
            text = text.replace(f'<@{user_id}>', f'@{username}')
        
        msg_ts = msg.get('ts')
        formatted_msg = {
            "timestamp": format_timestamp(msg_ts),
            "text": text,
        }
        
        thread_ts = msg.get('thread_ts')
        if thread_ts and thread_ts != msg_ts:
            organized[ch_name]["threads"][thread_ts][msg_ts] = formatted_msg
        else:
            organized[ch_name]["messages"][msg_ts] = formatted_msg
    
    # Convert to final format
    result = {}
    for ch_name, data in organized.items():
        messages_list = list(data["messages"].values())
        threads_dict = {k: list(v.values()) for k, v in data["threads"].items()}
        result[ch_name] = {
            "messages": sorted(messages_list, key=lambda x: x["timestamp"]),
            "threads": {k: sorted(v, key=lambda x: x["timestamp"]) for k, v in threads_dict.items()}
        }
    
    return result, channels, users


def to_text(data: dict) -> str:
    lines = []
    for channel_name, channel_data in sorted(data.items()):
        lines.append(f"\n{'='*60}")
        lines.append(f"# Channel: #{channel_name}")
        lines.append('='*60 + "\n")
        for msg in channel_data["messages"]:
            lines.append(f"[{msg['timestamp']}] {msg['text']}")
        lines.append("")
    return "\n".join(lines)


# File upload
uploaded_file = st.file_uploader("Upload slackdump sqlite file", type=['sqlite', 'db'])

if uploaded_file:
    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.sqlite') as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name
    
    with st.spinner("Extracting messages..."):
        data, channels, users = extract_data(tmp_path)
    
    # Summary
    st.success("✅ Extraction complete!")
    
    st.subheader("📊 Summary")
    total = 0
    summary_data = []
    for ch, ch_data in sorted(data.items()):
        count = len(ch_data['messages'])
        total += count
        summary_data.append({"Channel": f"#{ch}", "Messages": count})
    
    st.table(summary_data)
    st.metric("Total Messages", total)
    
    # Downloads
    st.subheader("📥 Download")
    
    col1, col2 = st.columns(2)
    
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    col1.download_button(
        label="⬇️ Download JSON",
        data=json_str,
        file_name="slack_messages.json",
        mime="application/json"
    )
    
    text_str = to_text(data)
    col2.download_button(
        label="⬇️ Download TXT",
        data=text_str,
        file_name="slack_messages.txt",
        mime="text/plain"
    )
    
    # Preview
    with st.expander("👀 Preview JSON"):
        st.json(data)
    
    # Cleanup
    Path(tmp_path).unlink(missing_ok=True)

else:
    st.info("👆 Upload a sqlite file to get started")
    
st.divider()
st.caption("Built for Kedro team | Extracts messages from slackdump archives")
