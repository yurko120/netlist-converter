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
            line = line.strip()
            if not line or line.startswith('%'):
                continue
            
            upper_line = line.upper()
            
            # Detect Sections
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
                    # Clean package name: replace dots with underscores
                    pkg_raw = parts[0].replace('!', '').replace(';', '').replace('.', '_')
                    val = parts[1].replace(';', '')
                    des = parts[-1].replace(';', '')
                    packages.append(f"!{pkg_raw}! {val}; {des}")

            # --- PROCESS NETS (Rule of 10 Logic) ---
            elif zone == "END":
                # Clean the line from existing semicolons, commas, and asterisks
                clean_line = line.replace(',', ' ').replace(';', ' ').replace('*', ' ')
                parts = clean_line.split()
                
                if not parts:
                    continue

                # Identification: If line starts with no leading space/asterisk, it's a Net Name
                if not line.startswith((' ', '\t', '*')):
                    current_net = parts[0]
                    if current_net not in nets_data:
                        nets_data[current_net] = []
                    # The rest of the parts on this line are pins
                    nets_data[current_net].extend(parts[1:])
                else:
                    # Continuation line: all parts are pins for the current net
                    if current_net:
                        nets_data[current_net].extend(parts)

        # --- REBUILD FILE STRUCTURE ---
        final_output = ["$PACKAGES"]
        final_output.extend(packages)
        final_output.append("$NETS")
        
        for net_name, pins in nets_data.items():
            actual_pins = [p for p in pins if p.strip()]
            if not actual_pins:
                continue
            
            # Force "Rule of 10": Every line must start with [NetName];
            for i in range(0, len(actual_pins), 10):
                chunk = actual_pins[i:i+10]
                final_output.append(f"{net_name}; {' '.join(chunk)}")
        
        final_output.append("$End")
        all_results.append("\n".join(final_output))

    return "\n\n".join(all_results)

# --- STREAMLIT UI ---
st.set_page_config(page_title="Netlist Converter", layout="wide")

st.title("⚡ Netlist Converter (Allegro Format)")
st.write("Converts Altium .NET files. Rule of 10 is applied to all nets.")

uploaded_files = st.file_uploader("Upload .NET files", accept_multiple_files=True)

if uploaded_files:
    result_text = process_netlist_logic(uploaded_files)
    
    st.success("Files processed successfully!")
    
    # Live Preview Section
    st.subheader("🔍 Preview (Top 100 lines)")
    st.text_area("Review the formatting below:", 
                 value="\n".join(result_text.splitlines()[:100]), 
                 height=400)
    
    # Download Button
    st.download_button(
        label="📥 Download Converted Netlist",
        data=result_text,
        file_name="converted_netlist.txt",
        mime="text/plain"
    )
