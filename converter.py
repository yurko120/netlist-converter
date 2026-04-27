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
                    pkg_raw = parts[0].replace('!', '').replace(';', '').replace('.', '_')
                    pkg_str = f"!{pkg_raw}!"
                    if len(parts) >= 3:
                        val = parts[1].replace(';', '')
                        des = parts[-1].replace(';', '')
                        packages.append(f"{pkg_str} {val}; {des}")
                    else:
                        des = parts[1].replace(';', '')
                        packages.append(f"{pkg_str}; {des}")

            elif zone == "END":
                # Handle lines starting with * (continuation of a net)
                if line.startswith('*'):
                    if current_net:
                        # Extract pins, removing commas or semicolons
                        pins = line[1:].replace(',', ' ').replace(';', ' ').split()
                        nets_data[current_net].extend(pins)
                else:
                    # New net definition
                    parts = line.replace(',', ' ').split()
                    if parts:
                        # First part is the net name (clean semicolon if attached)
                        net_name = parts[0].split(';')[0].strip()
                        current_net = net_name
                        if current_net not in nets_data:
                            nets_data[current_net] = []
                        # Remaining parts are pins
                        pins = " ".join(parts[1:]).replace(';', ' ').split()
                        nets_data[current_net].extend(pins)

        final_output.append("$PACKAGES")
        final_output.extend(packages)
        final_output.append("$NETS")
        
        for net_name, pins in nets_data.items():
            # RULE OF 10: Force splitting pins into chunks of 10
            # Every single line will start with NetName;
            if not pins:
                continue
            for i in range(0, len(pins), 10):
                chunk = pins[i:i+10]
                final_output.append(f"{net_name}; {' '.join(chunk)}")
        
        final_output.append("$End")

    return "\n".join(final_output)

st.set_page_config(page_title="Netlist Converter", page_icon="⚡")
st.title("⚡ Altium to Allegro Netlist Converter")
st.write("Convert .NET files to Allegro format with Rule of 10 for Nets.")

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
