# import libraries
import gpiozero as gpio0
import glob
import time
import sys
import os

import Neuronetwork.main as nn_controller, Neuronetwork.training as nn_training
import multiprocessing
import numpy

import requests



# set server url
url = 'https://thermi.pythonanywhere.com/'

# get connection status from server
def get_connection_status():
    url = 'https://thermi.pythonanywhere.com/status'
    try:
        response = requests.get(url, timeout=(1.5, 2))
    except Exception as e:
        return 'Error'
    if response.text == "ok":
        return True
    else:
        return False




# Connection to the temperature sensor
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'


# Opening a data file
def read_temp_raw():
    with open(device_file, 'r') as f:
        return f.readlines()

# Temperature reading
def read_temp():
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos + 2:]
        temp_c = float(temp_string) / 1000.0
        return round(temp_c, 1)



# update training data in training.py
def update_training_data(heater_on_temp, max_reached_temp, heater_off_temp):
    nn_training.training_inputs = numpy.append(
        nn_training.training_inputs,
        [[heater_on_temp, max_reached_temp]],
        axis=0
    )

    nn_training.training_outputs = numpy.append(
        nn_training.training_outputs,
        [[heater_off_temp]],
        axis=0
    )

    nn_training.training_inputs16 = nn_training.training_inputs[-16:]
    nn_training.training_outputs16 = nn_training.training_outputs[-16:]

    nn_training.X_mean = numpy.mean(nn_training.training_inputs16, axis=0)
    nn_training.X_std = numpy.std(nn_training.training_inputs16, axis=0)
    nn_training.y_mean = numpy.mean(nn_training.training_outputs16)
    nn_training.y_std = numpy.std(nn_training.training_outputs16)

    nn_training.training_inputs_norm = (nn_training.training_inputs16 - nn_training.X_mean) / nn_training.X_std
    nn_training.training_outputs_norm = (nn_training.training_outputs16 - nn_training.y_mean) / nn_training.y_std

    numpy.savez('Neuronetwork/data normalization/data.npz', x_mean=nn_training.X_mean, x_std=nn_training.X_std, y_mean=nn_training.y_mean, y_std=nn_training.y_std)


heater_gpio = gpio0.LED(23)    # Heater relay control pin
heating = False  # Heater status flag


# Prompt user to set the temperature range
# print(f"Current temperature: {read_temp()}")
# print("Enter the temperature range to maintain:")
# min_temp = float(input("Minimum value: "))
# max_temp = float(input("Maximum value: "))



# ----- Initialization of variables -----

min_temp, max_temp = None, None
# --- Temperature control variables ---
heater_off_temp = None  # calculated heater switch-off temperature

max_reached_temp = None  # maximum temperature reached after heating
last_max_reached_temp = None  # previous maximum temperature
heater_on_temp = None  # temperature at which the heater was turned on
predicted_off_temp = None

are_temp_lims_setted = False

# --- Temperature history ---
temps = None  # list of measured temperatures
write_temp_to_list = True

# --- Neural network training state ---
wait_for_train_end = False  # indicates whether NN training is in progress


if __name__ == '__main__':
    try:
        if get_connection_status() == True:
            control_mode = requests.get(url + 'get-control-mode')

            if control_mode.json()['mode'] == 'auto' and control_mode.json()['temp_limits']:
                min_temp, max_temp = control_mode.json()['temp_limits']
                heater_off_temp = max_temp

                max_reached_temp = max_temp
                last_max_reached_temp = 0
                heater_on_temp = min_temp

                temps = [max_temp]

    except Exception as e:
        print(e)
        sys.exit()

    conn_main, conn_worker = multiprocessing.Pipe()     # creating pipe with training process

    while True:
        try:
            # Read current temperature
            curr_temp = read_temp()
            print(f'Temperature: {curr_temp} °C')

            # connect to the server and getting information
            try:
                if get_connection_status() == True:
                    requests.post(url+'send-temp', json={'temperature' : curr_temp})

                    control_mode = requests.get(url+'get-control-mode').json()

            except Exception as e:
                print(e)



            # if write_temp_to_list and temps:
            #     temps.append(curr_temp)


            # print(control_mode)
            # print(heating)
            if control_mode['mode'] == 'auto':      # check control mode
                are_temp_lims_setted = bool(control_mode['temp_limits'])
                # print(are_temp_lims_setted, control_mode['temp_limits'])

                # check if temperature limits are set by the user
                if are_temp_lims_setted:
                    min_temp, max_temp = control_mode['temp_limits']    # getting temperature limits


                    # initialization of variables
                    if heater_off_temp is None:
                        heater_off_temp = max_temp
                        temps = [max_temp]
                    if max_reached_temp is None:
                        max_reached_temp = max_temp
                    if last_max_reached_temp is None:
                        last_max_reached_temp = max_temp



                    # --- Heater ON condition ---
                    if curr_temp < min_temp and not heating:
                        heating = True
                        heater_gpio.on()
                        print('HEATER ON\n')

                        heater_on_temp = curr_temp

                        # Predict heater switch-off temperature using NN
                        heater_off_temp = nn_controller.get_off_temp(
                            [curr_temp, max_temp]
                        )
                        heater_off_temp = round(heater_off_temp, 1)
                        predicted_off_temp = heater_off_temp
                        print(f"Predicted off temperature: {heater_off_temp}\n")

                    # --- Heater OFF condition ---
                    if curr_temp >= heater_off_temp and heating:
                        heating = False
                        heater_gpio.off()
                        print('HEATER OFF\n')

                    # --- Detect temperature peak after heater shutdown ---
                    if max(temps) > curr_temp and curr_temp >= max_temp:
                        max_reached_temp = max(temps)

                        print("Temperature drops.")

                        # New peak detected → add training sample
                        if abs(max_reached_temp - last_max_reached_temp) >= 0.09 and not wait_for_train_end:
                            last_max_reached_temp = max_reached_temp

                            update_training_data(heater_on_temp, max_reached_temp, heater_off_temp)

                            print("Started training process.")

                            # Start NN training in a separate process
                            training_process = multiprocessing.Process(
                                target=nn_training.train,
                                args=(conn_worker,)
                            )
                            training_process.start()
                            wait_for_train_end = True

                        # Reset temperature history
                        temps.clear()
                        temps.append(max_temp)


                print(f'Heater on temp: {heater_on_temp}, max temp: {max_temp}, heater off temp: {heater_off_temp}, predicted temp: {predicted_off_temp}')
                print(f'Max reached temp: {max_reached_temp}, temp lims = {[min_temp, max_temp]}')


                # --- Handle NN training result ---
                if wait_for_train_end:
                    if conn_main.poll(0.2):     # check for training completion
                        msg = conn_main.recv()

                        if msg == 'Success':
                            print("Neural network training complete.")
                            wait_for_train_end = False

                            # Update NN weights
                            weights = nn_controller.update_weights()
                            (
                                nn_controller.ji_weights,
                                nn_controller.yj_weights,
                                nn_controller.bias_weights_j,
                                nn_controller.bias_weights_y
                            ) = weights
                            print("Weights updated.")

                        elif msg == 'Error':
                            print("Recived error message.\n")
                            wait_for_train_end = False
            elif control_mode['mode'] == 'manual':
                try:
                    if control_mode['heater_on']:
                        heating = True
                        heater_gpio.on()
                        print('HEATER ON\n')
                    elif not control_mode['heater_on']:
                        heating = False
                        heater_gpio.off()
                        print('HEATER OFF\n')

                except Exception as e:
                    pass

            time.sleep(.1)

        except Exception as e:
            print("Error:", e)
            time.sleep(1)
