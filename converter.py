import streamlit as st
import io

def process_netlist_logic(uploaded_files):
    all_results = []
    
    for uploaded_file in uploaded_files:
        content = uploaded_file.getvalue().decode('cp1255', errors='ignore')
        lines = [line.strip() for line in content.splitlines()]

        zone = None
        packages = []
        nets_data = {}
        current_net = None

        for line in lines:
            upper_line = line.upper()
            if "PART" in upper_line or "PACKAGES" in upper_line:
                zone = "START"
                continue
            elif "NET" in upper_line or "$NETS" in upper_line:
                zone = "END"
                continue
            
            if not line or line.startswith('%') or line.upper() == "$END":
                continue

            # --- PACKAGES ---
            if zone == "START":
                parts = [p for p in line.split(' ') if p]
                if len(parts) >= 2:
                    pkg_raw = parts[0].replace('!', '').replace(';', '').replace('.', '_')
                    pkg_str = f"!{pkg_raw}!"
                    if len(parts) >= 3:
                        val = parts[1].replace(';', '')
                        des = parts[-1].replace(';', '')
                        packages.append(f"{pkg_str} {val}; {des}")
                    else:
                        des = parts[1].replace(';', '')
                        packages.append(f"{pkg_str}; {des}")

            # --- NETS (The Fix is here) ---
            elif zone == "END":
                # Remove all semicolons and commas from the line first
                clean_line = line.replace(';', ' ').replace(',', ' ')
                
                if line.startswith('*'):
                    if current_net:
                        new_pins = clean_line[1:].strip().split()
                        nets_data[current_net].extend(new_pins)
                else:
                    parts = clean_line.split()
                    if parts:
                        # The first part is ALWAYS the Net Name
                        net_name = parts[0].strip()
                        current_net = net_name
                        if current_net not in nets_data:
                            nets_data[current_net] = []
                        # The rest are pins
                        new_pins = parts[1:]
                        nets_data[current_net].extend(new_pins)

        # --- REBUILDING THE FILE ---
        final_output = ["$PACKAGES"]
        final_output.extend(packages)
        final_output.append("$NETS")
        
        for net_name, pins in nets_data.items():
            # Filter out empty entries and clean any leftover characters
            actual_pins = [p.strip() for p in pins if p.strip() and p.strip() != ';']
            
            if not actual_pins:
                continue
            
            # MANDATORY RULE: Every line starts with [NetName]; and then max 10 pins
            for i in range(0, len(actual_pins), 10):
                chunk = actual_pins[i:i+10]
                # We put the semicolon ONLY after the net name
                final_output.append(f"{net_name}; {' '.join(chunk)}")
        
        final_output.append("$End")
        all_results.append("\n".join(final_output))

    return "\n\n".join(all_results)

# --- UI ---
st.set_page_config(page_title="Netlist Converter", page_icon="⚡", layout="wide")
st.title("⚡ Netlist Converter (Fixed Semicolon Logic)")

uploaded_files = st.file_uploader("Upload .NET files", accept_multiple_files=True)

if uploaded_files:
    result_text = process_netlist_logic(uploaded_files)
    st.success("Processed! Check the preview below:")
    
    # Preview to verify the GND; fix
    st.subheader("🔍 Preview (GND; Check)")
    st.text_area("Final Output Preview:", value="\n".join(result_text.splitlines()[:100]), height=400)
    
    st.download_button(
        label="📥 Download Converted Netlist",
        data=result_text,
        file_name="converted_netlist.txt",
        mime="text/plain"
    )
