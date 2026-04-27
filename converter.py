import streamlit as st
import io

def process_netlist_logic(uploaded_files):
    final_output = []
    
    for uploaded_file in uploaded_files:
        # Hebrew support encoding
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
            
            if not line or line.startswith('%'):
                continue

            if zone == "START":
                parts = [p for p in line.split(' ') if p]
                if len(parts) >= 2:
                    # REPLACE DOTS WITH UNDERSCORES IN PACKAGE NAME
                    pkg_raw = parts[0].replace('!', '').replace(';', '').replace('.', '_')
                    pkg_str = f"!{pkg_raw}!"
                    
                    if len(parts) >= 3:
                        val = parts[1].replace(';', '')
                        des = parts[-1].replace(';', '')
                        packages.append(f"{pkg_str} {val} ; {des}")
                    else:
                        des = parts[1].replace(';', '')
                        packages.append(f"{pkg_str} ; {des}")

            elif zone == "END":
                clean_line = line.replace('-', '.') 
                
                if clean_line.startswith('*'):
                    if current_net:
                        pins = clean_line[1:].strip().replace(',', ' ').split()
                        nets_data[current_net].extend(pins)
                else:
                    parts = clean_line.split()
                    if parts:
                        current_net = parts[0].replace(';', '')
                        pins = " ".join(parts[1:]).replace(',', ' ').split()
                        if current_net not in nets_data:
                            nets_data[current_net] = []
                        nets_data[current_net].extend(pins)

        final_output.append("$PACKAGES")
        final_output.extend(packages)
        final_output.append("$NETS")
        
        for net_name, pins in nets_data.items():
            for i in range(0, len(pins), 10): # Rule of 10
                chunk = pins[i:i+10]
                final_output.append(f"{net_name} ; {' '.join(chunk)}")
        
        final_output.append("$End")

    return "\n".join(final_output)

# Website UI
st.set_page_config(page_title="Netlist Converter", page_icon="⚡")
st.title("⚡ Altium to Allegro Converter")
st.write("Drag and drop your .net files below.")

uploaded_files = st.file_uploader("Upload NET files", accept_multiple_files=True)

if uploaded_files:
    result_text = process_netlist_logic(uploaded_files)
    st.success(f"Processed {len(uploaded_files)} file(s) successfully!")
    st.download_button(
        label="📥 Download Converted Netlist",
        data=result_text,
        file_name="converted_netlist.txt",
        mime="text/plain"
    )
