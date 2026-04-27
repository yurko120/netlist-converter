import streamlit as st
import io

def process_netlist_logic(uploaded_files):
    final_output = []
    
    for uploaded_file in uploaded_files:
        # Handling encoding for potential Hebrew characters in original file
        content = uploaded_file.getvalue().decode('cp1255', errors='ignore')
        lines = [line.strip() for line in content.splitlines()]

        zone = None
        packages = []
        nets_data = {}
        current_net = None

        for line in lines:
            upper_line = line.upper()
            
            # Identify Zones
            if "PART" in upper_line or "PACKAGES" in upper_line:
                zone = "START"
                continue
            elif "NET" in upper_line or "$NETS" in upper_line:
                zone = "END"
                continue
            
            # Skip empty lines or comments
            if not line or line.startswith('%'):
                continue

            # Process $PACKAGES Zone
            if zone == "START":
                parts = [p for p in line.split(' ') if p]
                if len(parts) >= 2:
                    # Clean Package Name: Replace dots with underscores
                    pkg_raw = parts[0].replace('!', '').replace(';', '').replace('.', '_')
                    pkg_str = f"!{pkg_raw}!"
                    
                    if len(parts) >= 3:
                        val = parts[1].replace(';', '')
                        des = parts[-1].replace(';', '')
                        # Fix: semicolon attached to value
                        packages.append(f"{pkg_str} {val}; {des}")
                    else:
                        des = parts[1].replace(';', '')
                        packages.append(f"{pkg_str}; {des}")

            # Process $NETS Zone
            elif zone == "END":
                clean_line = line.replace('-', '.')
                if clean_line.startswith('*'):
                    if current_net:
                        pins = clean_line[1:].strip().replace(',', ' ').split()
                        nets_data[current_net].extend(pins)
                else:
                    parts = clean_line.split()
                    if parts:
                        # Clean net name and ensure semicolon is attached
                        net_name = parts[0].split(';')[0].strip()
                        current_net = net_name
                        pins = " ".join(parts[1:]).replace(';', ' ').replace(',', ' ').split()
                        if current_net not in nets_data:
                            nets_data[current_net] = []
                        nets_data[current_net].extend(pins)

        # Build Final File Structure
        final_output.append("$PACKAGES")
        final_output.extend(packages)
        final_output.append("$NETS")
        
        for net_name, pins in nets_data.items():
            # Rule of 10: Every line starts with NetName; followed by up to 10 pins
            for i in range(0, len(pins), 10):
                chunk = pins[i:i+10]
                final_output.append(f"{net_name}; {' '.join(chunk)}")
        
        final_output.append("$End")

    return "\n".join(final_output)

# Streamlit UI Configuration
st.set_page_config(page_title="Netlist Converter", page_icon="⚡")
st.title("⚡ Altium to Allegro Netlist Converter")
st.write("Upload your .NET files to convert them to Allegro format.")

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
