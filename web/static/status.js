var KNOWN_SYSTEMS = {};

function bytes_to_gb(value) {
    return ((( value  / 1024.0) / 1024) / 1024).toFixed(2);
}

function update_system_info() {
    const http = new XMLHttpRequest();

    http.onreadystatechange = (e) => {
        if (http.readyState == 4) {
            system_data = JSON.parse(http.responseText); 

            document.getElementById("system_name").textContent = system_data['system'];
            document.getElementById("cpu_percent").setAttribute("value", system_data['cpu_percent']);
            if (system_data['cpu_percent'] < 60.0) {
                document.getElementById("cpu_percent").setAttribute("class", 'tertiary');
            } else {
                document.getElementById("cpu_percent").setAttribute("class", 'secondary');
            }

            var total_mem_gb = bytes_to_gb(system_data['memory_total']);
            var used_mem_gb = bytes_to_gb(system_data['memory_used'])
            document.getElementById("mem_details").textContent = used_mem_gb + " GB/" + total_mem_gb + " GB";


            var mem_percent = (((system_data['memory_used']+0.0) / system_data['memory_total']) * 100.0 ).toFixed(2);
            document.getElementById("mem_percent").setAttribute("value", mem_percent);
            if (mem_percent < 75.0) {
                document.getElementById("mem_percent").setAttribute("class", 'tertiary');
            } else {
                document.getElementById("mem_percent").setAttribute("class", 'secondary');
            }

            var disk_total = bytes_to_gb(system_data['disk_total']);
            var disk_used = bytes_to_gb(system_data['disk_used']);
            var disk_percent = (((system_data['disk_used']+0.0) / system_data['disk_total']) * 100.0 ).toFixed(2);
            document.getElementById("disk_percent").setAttribute("value", disk_percent);
            document.getElementById("disk_details").textContent = disk_used + " GB/" + disk_total + " GB";
            if (disk_percent < 80.0) {
                document.getElementById("disk_percent").setAttribute("class", 'tertiary');
            } else {
                document.getElementById("disk_percent").setAttribute("class", 'secondary');
            }

        }
    }

    http.open("GET", 'api/v1/_system_data');
    http.send();
}

function update_server_list() {
    // 
    const http = new XMLHttpRequest();

    http.onreadystatechange = (e) => {
        if (http.readyState == 4) {
            var response = JSON.parse(http.responseText); 
            var system_list = response['result']['servers'];
            
            console.log(system_list);

            for (var i = 0; i < system_list.length; i++) {
                var id = system_list[i][0] + "-" + system_list[i][1];
                console.log(id);
                var row = system_list[i];

                if (!(id in KNOWN_SYSTEMS)) {
                    
                    row[5] = true;
                    KNOWN_SYSTEMS[id] = row;

                    var new_system = document.createElement('tr');
                    new_system.setAttribute("id", id);
                    for (var j = 0; j < 5; j++) {
                        var cell = document.createElement('td');
                        cell.innerHTML = row[j];
                        new_system.appendChild(cell);
                        if (j == 4) {
                            cell.setAttribute("id", id + "-status");
                        }
                    }
                    document.getElementById('system_list').appendChild(new_system);
                } else {
                    if (KNOWN_SYSTEMS[id][4] != row[4]) {
                        document.getElementById(id + "-status").innerHTML = row[4];
                        KNOWN_SYSTEMS[id][4] = row[4];
                    }
                    KNOWN_SYSTEMS[id][5] = true;
                }
            }

            for (var key in KNOWN_SYSTEMS) {
                if (KNOWN_SYSTEMS[key][5] != true) {
                    console.log("Removing " + key);
                    delete KNOWN_SYSTEMS[key];
                    var elem = document.getElementById(key);
                    elem.parentNode.removeChild(elem);
                }
            }

        }
    }

    http.open("GET", '/api/v1/_servers/list_all');
    http.send();
}

update_system_info();
setInterval(update_system_info, 3000);

update_server_list();
setInterval(update_server_list, 7000);
