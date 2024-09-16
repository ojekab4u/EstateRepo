   <script>
            function initializeAutocomplete(inputId) {
                var input = document.getElementById(inputId);
                var autocomplete = new google.maps.places.Autocomplete(input);
                autocomplete.setFields(['address_components', 'geometry', 'icon', 'name']);
            }
    
            function initAutocomplete() {
                var inputs = document.getElementsByClassName('autocomplete');
                for (var i = 0; i < inputs.length; i++) {
                    initializeAutocomplete(inputs[i].id);
                }
            }
            
            



            
            function updateVehicleFields() {
                var numCars = document.getElementById('num_cars').value;
                var vehicleFieldsContainer = document.getElementById('vehicle-fields');
                vehicleFieldsContainer.innerHTML = '';
    
                for (var i = 1; i <= numCars; i++) {
                    vehicleFieldsContainer.innerHTML += `
                    <div>
                        {% if vehicles.exists %}
                        <h3>Vehicle ${i}</h3>
                        <label for="vehicle_${i}">Vehicle:</label>   
                        <select id="vehicle_${i}" name="vehicle_${i}" class="form-control " required>
                        <option value="" disabled selected>Select a Vehicle</option>
                        
                        {% for vehicle in vehicles %}
                            <option value="{{ vehicle.id }}">{{ vehicle.name }}/{{vehicle.fuel_consumption_rate}}</option>
                        {% endfor %}

                        {% comment %} <option value="add">Add More Vehicle</option> {% endcomment %}

                        </select><br/>
                        
                        {% else %}
                        <!-- If no vehicles are created, show a link to add a vehicle -->
                        <p>You have not added any vehicles yet. <a href="{% url 'add_vehicle' %}">Click here to add a vehicle.</a></p>
                        {% endif %}

                        <label for="work_location_${i}">Work Location:</label>
                        <input type="text" id="work_location_${i}" name="work_location_${i}" class="autocomplete form-control" required><br/>

                        <label for="work_trips_per_week_${i}">Trips per Week:</label>
                        <input type="number" id="work_trips_per_week_${i}" name="work_trips_per_week_${i}" value="5" min="1" class="form-control" required><br/>

                        <!-- Other Locations Section -->
                        <div id="other-locations-container-${i}">
                            <div id="additional-locations-${i}"></div>
                            <button type="button" class="btn btn-secondary mb-3" onclick="addLocationField(${i})">Add Other Location</button>
                        </div>
                    </div>
                    `;
                }
                initAutocomplete();
            }
            document.getElementById("vehicle_{{ i }}").addEventListener("change", function() {
                if (this.value === "add") {
                    window.location.href = "{% url 'add_vehicle' %}";
                }
            });
            function addLocationField(vehicleIndex) {
                let container = document.getElementById(`additional-locations-${vehicleIndex}`);
                let index = container.children.length;
                let locationHtml = `
                    <div class="location-field mb-3">
                        <label for="location_name_${vehicleIndex}_${index}">Location Name:</label>
                        <input type="text" id="location_name_${vehicleIndex}_${index}" name="location_name_${vehicleIndex}_${index}" class="form-control" placeholder="e.g. Church, Market">
                        
                        <label for="location_address_${vehicleIndex}_${index}">Address:</label>
                        <input type="text" id="location_address_${vehicleIndex}_${index}" name="location_address_${vehicleIndex}_${index}" class="autocomplete form-control" required>
                        
                        <label for="location_trips_per_week_${vehicleIndex}_${index}">Trips per Week:</label>
                        <input type="number" id="location_trips_per_week_${vehicleIndex}_${index}" name="location_trips_per_week_${vehicleIndex}_${index}" value="1" class="form-control" min="1" required>
                    </div>
                `;
                container.insertAdjacentHTML('beforeend', locationHtml);
                initAutocomplete();
            }

            
        </script>