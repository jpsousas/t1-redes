from scapy.all import ARP, rdpcap
from collections import Counter
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import json
import requests

# Read the pcap file to extract MAC addresses
packets = rdpcap('arp.pcap')
mac_addresses = [packet.hwsrc for packet in packets if ARP in packet]
counter = Counter(mac_addresses)

def get_response_from_mac_api(mac_address):
    url = f"https://api.maclookup.app/v2/macs/{mac_address}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def get_mac_details(mac_address):
    response_body = get_response_from_mac_api(mac_address)
    if response_body is None:
        return ("Not Found", "Not Found")
    company_name = response_body.get("company", "Not Found")
    country_iso = response_body.get("country", "Not Found")
    return (company_name, country_iso)

def get_country_flag_url(country_iso):
    if country_iso == "Not Found":
        return "https://via.placeholder.com/36x27?text=No+Flag"
    else:
        return f"https://flagcdn.com/36x27/{country_iso.lower()}.png"

# Fetching details for each MAC address
manufacturers_details = {mac: get_mac_details(mac) for mac in counter.keys()}

# Preparing manufacturer data for visualization
manufacturer_data = Counter(details[0] for details in manufacturers_details.values())

app = FastAPI()

@app.get("/manufacturers", response_class=HTMLResponse)
async def get_manufacturers():
    # Preparing data for the pie chart
    labels = list(manufacturer_data.keys())
    values = list(manufacturer_data.values())
    colors = [f'rgba({i % 255}, {(i+100) % 255}, {(i*30+150) % 255}, 0.6)' for i in range(len(labels))]

    # Generating HTML content for each manufacturer, including country flags
    manufacturers_html = ""
    for mac, (name, country_iso) in manufacturers_details.items():
        flag_url = get_country_flag_url(country_iso)
        manufacturers_html += f"""
        <div>
            <h3>{name} ({country_iso})</h3>
            <img src="{flag_url}" alt="Country Flag" style="height: 50px;">
        </div>
        """

    content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Manufacturer Distribution</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body>
        <h1>Manufacturer Distribution</h1>
        <div style="width:600px;">
            <canvas id="manufacturerChart"></canvas>
        </div>
        <script>
            var ctx = document.getElementById('manufacturerChart').getContext('2d');
            var manufacturerChart = new Chart(ctx, {{
                type: 'pie',
                data: {{
                    labels: {json.dumps(labels)},
                    datasets: [{{
                        label: 'Number of Devices',
                        data: {json.dumps(values)},
                        backgroundColor: {json.dumps(colors)},
                        borderColor: 'rgba(255, 255, 255, 1)',
                        borderWidth: 2
                    }}]
                }}
            }});
        </script>
        <h2>Manufacturer Details</h2>
        {manufacturers_html}
    </body>
    </html>
    """
    return content
