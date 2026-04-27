import streamlit as st
import io
import datetime

# --- CORE LOGIC ---
def process_netlist_logic(uploaded_files):
    all_results = []
    for uploaded_file in uploaded_files:
        content = uploaded_file.getvalue().decode('cp1255', errors='ignore')
        lines = content.splitlines()
        zone = None
        packages = []
        nets_data = {}
        current_net = None

        for line in lines:
            raw_line = line 
            line = line.strip()
            if not line or line.startswith('%'):
                continue
            upper_line = line.upper()
            if "PART" in upper_line or "PACKAGES" in upper_line:
                zone = "START"
                continue
            elif "NET" in upper_line or "$NETS" in upper_line:
                zone = "END"
                continue
            elif upper_line == "$END":
                zone = None
                continue

            if zone == "START":
                parts = line.split()
                if len(parts) >= 2:
                    pkg_raw = parts[0].replace('!', '').replace(';', '').replace('.', '_')
                    val = parts[1].replace(';', '')
                    des = parts[-1].replace(';', '')
                    packages.append(f"!{pkg_raw}! {val}; {des}")

            elif zone == "END":
                clean_line = line.replace(',', ' ').replace(';', ' ').replace('*', ' ')
                parts = clean_line.split()
                if not parts:
                    continue
                if not raw_line.startswith((' ', '\t', '*')):
                    current_net = parts[0]
                    if current_net not in nets_data:
                        nets_data[current_net] = []
                    nets_data[current_net].extend(parts[1:])
                else:
                    if current_net:
                        nets_data[current_net].extend(parts)

        final_output = ["$PACKAGES"]
        final_output.extend(packages)
        final_output.append("$NETS")
        for net_name, pins in nets_data.items():
            actual_pins = [p.strip() for p in pins if p.strip() and p.strip() != ';']
            if not actual_pins: continue
            for i in range(0, len(actual_pins), 10):
                chunk = actual_pins[i:i+10]
                final_output.append(f"{net_name}; {' '.join(chunk)}")
        final_output.append("$End")
        all_results.append("\n".join(final_output))
    return "\n\n".join(all_results)

# --- UI LAYOUT ---
st.set_page_config(page_title="Mind-Board Converter", layout="wide")

# Correct Direct Link for the Logo
logo_url = "https://raw.githubusercontent.com/yurko120/netlist-converter/main/.devcontainer/MindBoard-Logo.jpg"

st.markdown(f"""
    <style>
    /* Fixed background watermark - stays static on scroll */
    .stApp {{
        background-image: url("{logo_url}");
        background-repeat: no-repeat;
        background-attachment: fixed; /* Crucial: background does not move on scroll */
        background-position: center 30%; /* Raised up to blend with upload box */
        background-size: 35%; /* Optimal size */
    }}
    
    /* Overlay to make it 20% more transparent (approx 0.08 intensity) */
    .stApp::before {{
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background-color: rgba(255, 255, 255, 0.92); /* Higher white opacity for lighter logo */
        z-index: -1;
    }}

    /* Welcome header: Larger and slightly shifted left */
    .centered-title {{
        text-align: center;
        width: 100%;
        padding-top: 10px;
        padding-bottom: 20px;
        font-size: 3em !important; /* Larger text */
        margin-left: -5% !important; /* Shifted left */
        font-weight: 700;
        color: #1e1e1e;
    }}
    
    /* Ensure UI elements are above the watermark layer */
    .stMarkdown, .stFileUploader, .stButton, .stTextArea, .stSubheader, .stDivider {{
        position: relative;
        z-index: 10;
    }}
    </style>
    <h1 class="centered-title">Welcome to Mind-Board Converter</h1>
    """, unsafe_allow_html=True)

# Main structure
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### **Upload .NET files**")
    uploaded_files = st.file_uploader("", accept_multiple_files=True, label_visibility="collapsed")

if uploaded_files:
    result_text = process_netlist_logic(uploaded_files)
    
    with col2:
        st.subheader("File Settings")
        today = datetime.date.today().strftime("%d_%m_%Y")
        original_name = uploaded_files[0].name.rsplit('.', 1)[0]
        default_output_name = f"{original_name}_{today}"
        
        custom_name = st.text_input("Set output filename:", value=default_output_name)
        full_filename = custom_name if custom_name.endswith(('.txt', '.net')) else f"{custom_name}.txt"
        
        st.download_button(
            label=f"📥 Download {full_filename}",
            data=result_text,
            file_name=full_filename,
            mime="text/plain",
            use_container_width=True
        )

    st.divider()
    # The Subheader for Preview
    st.subheader("🔍 Full File Preview")
    # Displaying the entire result_text allows full scrolling while background stays fixed
    st.text_area("Final netlist structure:", value=result_text, height=600)
