import re

with open('core/static/js/req_banner.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix placement
content = content.replace("const form = subnetSelect.closest('form');", "const targetContainer = subnetSelect.closest('.card-body') || subnetSelect.closest('form');")
content = content.replace("if (form) {\n            form.appendChild(mapContainer);\n        }", "if (targetContainer) {\n            targetContainer.appendChild(mapContainer);\n        }")

# Replace the block string creation
# We will just replace the innerHTML creation for the block
old_block_code = '''html += '<div class="ip-block ' + (ip.status === 'available' ? 'ip-available' : '') + '" ' +
                            'data-id="' + ip.id + '" data-ip="' + ip.ip + '" data-status="' + ip.status + '" ' +
                            'title="' + ip.ip + ' (' + ip.status + ')" ' +
                            'style="width: 24px; height: 24px; background: ' + color + '; border-radius: 4px; cursor: ' + cursor + '; transition: transform 0.1s;" ' +
                            'onmouseover="this.style.transform=\\\'scale(1.2)\\\'" onmouseout="this.style.transform=\\\'scale(1)\\\'"></div>';'''

new_block_code = '''let lastOctet = ip.ip.split('.').pop();
                        html += '<div class="ip-block ' + (ip.status === 'available' ? 'ip-available' : '') + '" ' +
                            'data-id="' + ip.id + '" data-ip="' + ip.ip + '" data-status="' + ip.status + '" ' +
                            'title="' + ip.ip + ' (' + ip.status + ')" ' +
                            'style="width: 38px; height: 32px; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 600; color: white; background: ' + color + '; border-radius: 4px; cursor: ' + cursor + '; transition: transform 0.1s;" ' +
                            'onmouseover="this.style.transform=\\\'scale(1.2)\\\'" onmouseout="this.style.transform=\\\'scale(1)\\\'">' + lastOctet + '</div>';'''

# Because of escape sequences, just use regex to replace everything inside the forEach loop after setting color
regex = re.compile(r"html \+= '<div class=\"ip-block ' \+ \(ip\.status === 'available' \? 'ip-available' : ''\) \+ '\" ' \+.*?'></div>';", re.DOTALL)
content = regex.sub(new_block_code.replace('\\\'', "'"), content)

with open('core/static/js/req_banner.js', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
