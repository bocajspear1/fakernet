var module_map = {}

function clear_outputs() {
    var output = document.getElementById('output');
    var error_output = document.getElementById('error-out');

    output.innerHTML = "";
    error_output.innerHTML = "";   
    
    error_output.classList.add("hidden");
}

function run_module_function(module, func, data) {
    const http = new XMLHttpRequest();

    clear_outputs();

    http.onreadystatechange = (e) => {
        if (http.readyState == 4) {

            var wait_spinner2 = document.getElementById('wait-spinner');
            wait_spinner2.classList.add("hidden");

            response_data = JSON.parse(http.responseText);

            var output = document.getElementById('output');
            var error_output = document.getElementById('error-out');

            if (!response_data['ok']) {
                error_output.innerHTML = response_data['error'];
                error_output.removeAttribute("style");
            } else {
                error_output.classList.add("hidden");
                output.innerHTML = JSON.stringify(response_data['result'], null, 2);;
            }

        }
    }

    var wait_spinner = document.getElementById('wait-spinner');
    wait_spinner.classList.remove("hidden");

    var formData = new FormData();
    for (const property in data) {
        formData.set(property, data[property]);
    }

    http.open("POST", 'api/v1/' + module + '/run/' + func);
    http.send(formData);
}


function get_module_functions() {

    var module_select = document.getElementById('module-select');
    var function_select = document.getElementById('function-select');
    var submit_button = document.getElementById('submit-button');
    var param_inputs = document.getElementById('param-inputs');
    var func_desc = document.getElementById('func-desc');

    module_select.addEventListener("change", function(){
        if (module_select.value != "") {
            function_select.removeAttribute("disabled");

            clear_outputs();

            while (function_select.firstChild) {
                function_select.removeChild(function_select.firstChild);
            }
            while (param_inputs.firstChild) {
                param_inputs.removeChild(param_inputs.firstChild);
            }

            var default_func = document.createElement('option');
            default_func.setAttribute("value", "");
            default_func.innerHTML = "Select Function";
            function_select.appendChild(default_func);

            var function_data = module_map[module_select.value];
            var function_list = Object.keys(function_data);
            for (var i = 0; i < function_list.length; i++) {
                var module = function_list[i];
                var new_func = document.createElement('option');
                new_func.setAttribute("value", module);
                new_func.innerHTML = module;
                function_select.appendChild(new_func);
            }
            func_desc.innerHTML = "";
        } else {
            function_select.setAttribute("disabled", "disabled");
            submit_button.setAttribute("disabled", "disabled");
            func_desc.innerHTML = "";
        }
    });

    function_select.addEventListener("change", function(){
        if (function_select.value != "") {

            clear_outputs();

            while (param_inputs.firstChild) {
                param_inputs.removeChild(param_inputs.firstChild);
            }

            submit_button.removeAttribute("disabled");
            var param_data = module_map[module_select.value][function_select.value];
            var param_list = Object.keys(param_data);
            for (var i = 0; i < param_list.length; i++) {
                var param = param_list[i];
                if (param == "_desc") {
                    func_desc.innerHTML = param_data[param];
                } else {

                    var new_div = document.createElement('div');
                    new_div.setAttribute("class", 'input-group');

                    var new_label = document.createElement('label');
                    new_label.setAttribute("for", param);
                    new_label.innerHTML = param
                    new_div.appendChild(new_label);

                    if (!Array.isArray(param_data[param])) {
                        var new_param = document.createElement('input');
                        if (param_data[param] == "PASSWORD") {
                            new_param.setAttribute("type", "password");
                        } else {
                            new_param.setAttribute("type", "text");
                        }
                        new_param.setAttribute("id", "param-" + param);
                        new_div.appendChild(new_param);
                    } else {
                        var new_param = document.createElement('select');
                        new_param.setAttribute("id", "param-" + param);
                        for (var j = 0; j < param_data[param].length; j++) {
                            var new_option = document.createElement('option');
                            new_option.setAttribute("value", param_data[param][j]);
                            new_option.innerHTML = param_data[param][j];
                            new_param.appendChild(new_option);
                        }
                        new_div.appendChild(new_param);
                    }
                    param_inputs.appendChild(new_div);
                }
                
                
                
            }
        } else {
            submit_button.setAttribute("disabled", "disabled");
        }
    });

    submit_button.addEventListener("click", function() {
        var module_name = module_select.value;
        var function_name = function_select.value;

        
        if (module_name != "" && function_name != ""){
            
            clear_outputs();

            var param_values = {}
            var param_data = module_map[module_select.value][function_select.value];
            var param_list = Object.keys(param_data);
            for (var i = 0; i < param_list.length; i++) {
                var param = param_list[i]; 
                if (param != "_desc") {
                    param_values[param] = document.getElementById('param-' + param).value;
                }
            }
            run_module_function(module_name, function_name, param_values);
        }
    });

    const http = new XMLHttpRequest();

    http.timeout = 30000;

    http.onreadystatechange = (e) => {
        if (http.readyState == 4) {
            module_data = JSON.parse(http.responseText)['result']; 

            module_map = module_data;

            var modules_list = Object.keys(module_data);
            
            for (var i = 0; i < modules_list.length; i++) {
                var module = modules_list[i];
                var new_module = document.createElement('option');
                new_module.setAttribute("value", module);
                new_module.innerHTML = module;
                module_select.appendChild(new_module);
            }
            

        }
    }

    http.open("GET", 'api/v1/_modules/list');
    http.send();
}

get_module_functions();