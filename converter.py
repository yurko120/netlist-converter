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
                if line.startswith('*'):
                    if current_net:
                        # Add pins from continuation lines to the dictionary
                        pins = line[1:].replace(',', ' ').replace(';', ' ').split()
                        nets_data[current_net].extend(pins)
                else:
                    parts = line.replace(',', ' ').split()
                    if parts:
                        # Extract net name correctly without semicolon
                        net_name = parts[0].split(';')[0].strip()
                        current_net = net_name
                        if current_net not in nets_data:
                            nets_data[current_net] = []
                        # Add initial pins from the first net line
                        pins = " ".join(parts[1:]).replace(';', ' ').split()
                        nets_data[current_net].extend(pins)

        # Build the final document
        final_output.append("$PACKAGES")
        final_output.extend(packages)
        final_output.append("$NETS")
        
        for net_name, pins in nets_data.items():
            if not pins:
                continue
            
            # THE FIX: Split pins into chunks of 10
            # Each line starts with: NetName; Pin1 Pin2 ... Pin10
            for i in range(0, len(pins), 10):
                chunk = pins[i:i+10]
                line_content = f"{net_name}; {' '.join(chunk)}"
                final_output.append(line_content)
        
        final_output.append("$End")

    return "\n".join(final_output)

# UI Settings
st.set_page_config(page_title="Netlist Converter", page_icon="⚡")
st.title("⚡ Altium to Allegro Netlist Converter")
st.write("Convert .NET files with mandatory Net Name on every line (Rule of 10).")

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
