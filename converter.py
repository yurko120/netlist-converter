import streamlit as st
import io
import datetime

# --- CORE LOGIC ---
def process_single_file(uploaded_file):
    """Processes a single file and returns the transformed string."""
    content = uploaded_file.getvalue().decode('cp1255', errors='ignore')
    lines = content.splitlines()
    zone = None
    packages = []
    nets_data = {}
    current_net = None

    for line in lines:
        raw_line = line 
        line = line.strip()
        if not line:
            continue
            
        upper_line = line.upper()
        
        # 1. Zone Detection
        if any(k in upper_line for k in ["PART", "PACKAGES", "$PACKAGES"]):
            zone = "START"
            continue
        elif any(k in upper_line for k in ["$NETS", "NET"]):
            zone = "END"
            continue
        elif upper_line.startswith('$'):
            zone = None
            continue

        # 2. Extracting Packages
        if zone == "START":
            temp_line = line.replace('!', ' ').replace(';', ' ')
            parts = temp_line.split()
            
            if len(parts) >= 2:
                pkg_id = parts[0].replace('.', '_')
                des = parts[-1]
                
                if len(parts) > 2:
                    val = parts[1]
                    packages.append(f"!{pkg_id}! {val}; {des}")
                else:
                    packages.append(f"!{pkg_id}! ; {des}")

        # 3. Extracting Nets
        elif zone == "END":
            processed_line = line.replace('-', '.')
            clean_line = processed_line.replace(',', ' ').replace(';', ' ').replace('*', ' ')
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

    # Final Assembly for the file
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
    return "\n".join(final_output)

# --- UI LAYOUT ---
st.set_page_config(page_title="Mind-Board Converter", layout="wide")

logo_url = "https://raw.githubusercontent.com/yurko120/netlist-converter/main/.devcontainer/MindBoard-Logo.jpg"

st.markdown(f"""
    <style>
    .stApp {{
        background-image: url("{logo_url}");
        background-repeat: no-repeat;
        background-attachment: fixed;
        background-position: center 70%; 
        background-size: 45%; 
    }}
    
    .stApp::before {{
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background-color: rgba(255, 255, 255, 0.92); 
        z-index: -1;
    }}

    .centered-title {{
        text-align: center;
        color: #000000;
        font-size: 3.5em !important; 
        font-weight: 900 !important; 
        padding-top: 20px;
        padding-bottom: 50px;
    }}

    [data-testid="stTextInput"] label {{
        font-size: 1.1rem !important; 
        font-weight: 700 !important; 
        color: #000000 !important;
    }}

    .stTextArea textarea {{
        background-color: rgba(255, 255, 255, 0.6) !important; 
        border: 2px solid #000000 !important;
        border-radius: 10px;
        color: #000000 !important;
        font-family: 'Courier New', monospace;
        font-weight: 800 !important; 
        font-size: 1.1em !important;
    }}
    </style>
    <h1 class="centered-title">Welcome to Mind-Board Converter</h1>
    """, unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### **1. Upload Source Files**")
    uploaded_files = st.file_uploader("Upload .NET files", accept_multiple_files=True, label_visibility="collapsed")

if uploaded_files:
    processed_files_data = []
    
    with col2:
        st.markdown("### **2. File Settings & Download**")
        for idx, f in enumerate(uploaded_files):
            # Create an individual naming field for each file
            original_name = f.name.rsplit('.', 1)[0]
            custom_name = st.text_input(f"Name for file {idx+1} ({f.name}):", 
                                        value=f"{original_name}_transformed", 
                                        key=f"name_{idx}")
            
            # Process the file
            content = process_single_file(f)
            
            # Add to list for the Preview tabs
            processed_files_data.append({
                "display_name": custom_name,
                "content": content
            })
            
            # Download button for this specific file
            full_filename = custom_name if custom_name.endswith(('.txt', '.net')) else f"{custom_name}.txt"
            st.download_button(
                label=f"📥 Download {full_filename}",
                data=content,
                file_name=full_filename,
                mime="text/plain",
                key=f"dl_{idx}",
                use_container_width=True
            )
            st.write("---") # Visual separator between files

    st.divider()
    st.subheader("🔍 Technical Preview (Per File)")
    
    # Create Tabs based on the custom names provided
    tab_titles = [item["display_name"] for item in processed_files_data]
    tabs = st.tabs(tab_titles)
    
    for idx, tab in enumerate(tabs):
        with tab:
            st.text_area(f"Preview for: {processed_files_data[idx]['display_name']}", 
                         value=processed_files_data[idx]['content'], 
                         height=500, 
                         key=f"text_{idx}")
