import streamlit as st
import io

def process_netlist_logic(uploaded_files):
    final_output = []
    
    for uploaded_file in uploaded_files:
        content = uploaded_file.getvalue().decode('cp1255', errors='ignore')
        lines = [line.strip() for line in content.splitlines()]

        zone = None
        packages = []
        nets_data = {}
        current_net = None

        for line in lines:
            upper_line = line.upper()
            
            # Zone detection
            if "PART" in upper_line or "PACKAGES" in upper_line:
                zone = "START"
                continue
            elif "NET" in upper_line or "$NETS" in upper_line:
                zone = "END"
                continue
            
            if not line or line.startswith('%') or line.upper() == "$END":
                continue

            # --- PACKAGES ZONE ---
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

            # --- NETS ZONE ---
            elif zone == "END":
                # Cleaning line from legacy semicolons and commas
                clean_line = line.replace(',', ' ').replace(';', ' ')
                
                if line.startswith('*'):
                    if current_net:
                        new_pins = clean_line[1:].strip().split()
                        nets_data[current_net].extend(new_pins)
                else:
                    parts = clean_line.split()
                    if parts:
                        net_name = parts[0].strip()
                        current_net = net_name
                        if current_net not in nets_data:
                            nets_data[current_net] = []
                        new_pins = parts[1:]
                        nets_data[current_net].extend(new_pins)

        # --- FINAL ASSEMBLY ---
        final_output.append("$PACKAGES")
        final_output.extend(packages)
        final_output.append("$NETS")
        
        for net_name, pins in nets_data.items():
            # Remove any empty strings from pin list
            actual_pins = [p for p in pins if p.strip()]
            if not actual_pins:
                continue
            
            # MANDATORY RULE OF 10: Every line starts with NetName;
            for i in range(0, len(actual_pins), 10):
                chunk = actual_pins[i:i+10]
                # THIS IS THE KEY: Every line is built as [NetName]; [Pins]
                final_output.append(f"{net_name}; {' '.join(chunk)}")
        
        final_output.append("$End")

    return "\n".join(final_output)

# Streamlit Interface
st.set_page_config(page_title="Netlist Converter", page_icon="⚡")
st.title("⚡ Altium to Allegro Netlist Converter")
st.write("Mandatory Rule: Every line starts with Net Name (Max 10 pins per line).")

uploaded_files = st.file_uploader("Upload NET files", accept_multiple_files=True)

if uploaded_files:
    result_text = process_netlist_logic(uploaded_files)
    st.success(f"Successfully processed {len(uploaded_files)} file(s)!")
    st.download_button(
        label="📥 Download Converted Netlist",
        data=result_text,
        file_name="converted_netlist.txt",
        mime="text/plain"
    )
