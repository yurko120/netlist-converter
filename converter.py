import streamlit as st
import io

def process_netlist_logic(uploaded_files):
    all_results = []
    
    for uploaded_file in uploaded_files:
        # Handle encoding for original file
        content = uploaded_file.getvalue().decode('cp1255', errors='ignore')
        lines = content.splitlines()

        zone = None
        packages = []
        nets_data = {}
        current_net = None

        for line in lines:
            raw_line = line # Save original to check for leading spaces/tabs
            line = line.strip()
            if not line or line.startswith('%'):
                continue
            
            upper_line = line.upper()
            
            # Identify current block
            if "PART" in upper_line or "PACKAGES" in upper_line:
                zone = "START"
                continue
            elif "NET" in upper_line or "$NETS" in upper_line:
                zone = "END"
                continue
            elif upper_line == "$END":
                zone = None
                continue

            # --- PROCESS PACKAGES ---
            if zone == "START":
                parts = line.split()
                if len(parts) >= 2:
                    pkg_raw = parts[0].replace('!', '').replace(';', '').replace('.', '_')
                    val = parts[1].replace(';', '')
                    des = parts[-1].replace(';', '')
                    packages.append(f"!{pkg_raw}! {val}; {des}")

            # --- PROCESS NETS (The Rule of 10 Fix) ---
            elif zone == "END":
                # Clean existing markers
                clean_line = line.replace(',', ' ').replace(';', ' ').replace('*', ' ')
                parts = clean_line.split()
                if not parts:
                    continue

                # LOGIC: If a line has NO leading whitespace, it is a new Net Name
                if not raw_line.startswith((' ', '\t', '*')):
                    current_net = parts[0]
                    if current_net not in nets_data:
                        nets_data[current_net] = []
                    nets_data[current_net].extend(parts[1:])
                else:
                    # If it starts with space/tab/*, these are just pins for the current net
                    if current_net:
                        nets_data[current_net].extend(parts)

        # --- BUILD FINAL FILE ---
        final_output = ["$PACKAGES"]
        final_output.extend(packages)
        final_output.append("$NETS")
        
        for net_name, pins in nets_data.items():
            # Ensure no stray characters in pin list
            actual_pins = [p.strip() for p in pins if p.strip() and p.strip() != ';']
            
            if not actual_pins:
                continue
            
            # CHUNK LOGIC: Repeat the NetName; for every 10 pins
            for i in range(0, len(actual_pins), 10):
                chunk = actual_pins[i:i+10]
                final_output.append(f"{net_name}; {' '.join(chunk)}")
        
        final_output.append("$End")
        all_results.append("\n".join(final_output))

    return "\n\n".join(all_results)

# --- Streamlit UI (English) ---
st.set_page_config(page_title="Netlist Converter", layout="wide")
st.title("⚡ Allegro Netlist Converter")
st.write("Converts Altium files with a mandatory Rule of 10 for Nets.")

uploaded_files = st.file_uploader("Upload .NET files", accept_multiple_files=True)

if uploaded_files:
    result_text = process_netlist_logic(uploaded_files)
    st.success("Files processed successfully!")
    
    # Live Preview for Verification
    st.subheader("🔍 Layout Preview")
    st.text_area("Check format here before downloading:", 
                 value="\n".join(result_text.splitlines()[:100]), 
                 height=400)
    
    st.download_button(
        label="📥 Download Converted Netlist",
        data=result_text,
        file_name="converted_netlist.txt",
        mime="text/plain"
    )
