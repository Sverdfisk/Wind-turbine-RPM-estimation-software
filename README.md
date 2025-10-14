# Visual Monitoring System for Wind Turbine RPM Estimation

## Thesis:
"Operators monitoring noise from wind turbines often lack direct access to the turbines’ rotational speed (RPM) data. This master’s thesis aims to address that issue using Sony's IMX385LQR image sensor. 
The research will involve examining possible hardware configurations and exploring software techniques such as image processing. The project will culminate in a proof-of-concept with the goal of developing a prototype capable of monitoring the rotation of wind turbines and reporting their RPM over a given time interval."


## Intro
This repository provides RPM estimation software, Altium files for a custom PCB for the IMX385, and driver files. The driver files are for a Raspberry Pi 5 and works as a compatability layer for the image sensor to work properly. Each component of the project can be used on its own if desired. This means that the custom PCB, driver, or RPM detection software can be used without necessarily depending on the other modules.

### Notes and issues:
- The image pipeline (V4L2 pipeline) is not automatically set up, meaning that manual effort is required to fetch and encode frames. The driver/ folder provides some helpful scripts, but is not a complete configuration. The sensor can still send images to the Pi 5 as pixel data with no formatting.

## Setting up the hardware
- GPIO pins from the PCB to the Raspberry Pi need to be attached. The driver/ folder contains code to be run on the Pi, enabling the GPIO pins for the sensor in a strict, necessary sequence. See ```driver/imx-on.py``` for pin numbers and names. The GPIO pins used can in some cases be changed. If you need to change these values, ensure that pin compatability is retained by looking at the Pi 5's GPIO pinout.
- Ensure that the FFC is connected correctly on both the Pi and the custom PCB. The FFC pins should be pointing *towards* the PCB itself when connecting the cable, such that they are not visible when looking at the PCB from the top.
- **Important**: A small hack-job is required to connect the sequencer correctly. Use the ***SEQ*** test point on the PCB as an input voltage by attaching it to a GPIO pin on the Pi 5. In the default case, the imx-on.py file assumes it is connected to pin 26. Make sure you change this pin value in ```driver/imx-on.py``` if you choose another pin to connect it to.


## Installing the driver
- Installing the driver requires you to build and load the device tree and sensor driver files. A script that can be helpful is found in ```driver/compile.sh```. If you are unsure on how to compile and load drivers, consult official documentation. 
- **Ensure that the provided ```config.txt``` file located in ```driver/config.txt``` is used instead of the default ```/boot/firmware/config.txt``` on the Raspberry Pi 5**.

## Using the software
The code requires a camera or an input video. The feed path is specified in a config file as "target" and the RPM is then calculated.
Read "Initial setup" first. If you are deploying the system, read "Deployment mode". If you are testing, modifying, or configuring RPM estimation parameters, read "Testing mode".

### Initial setup
1. Clone the project
2. Enter the software folder
In this folder, you will see everything that is needed if you are simulating a video feed or if you are configurating the project.
The ```config_generator.py``` file is an application with a GUI that allows you to generate video feed configs. 
main.py is the main program runner, used to start monitoring RPM.
environment.txt is a conda environment file.

**If you are using your own custom environment:**
Look for ```environment.yml``` or ```requirements.txt```. Download the required modules using the module manager of your choice (such as pip). 

**If you are using Conda:** 
Conda can read the ```environment.yml``` file. Run the following command:
```conda env create -f environment.yml```


To start, the program needs some parameters to start detection such as where to look for a video stream. This can all be done through ```config_generator.py```, through manual tinkering, or both. It's recommended to first generate a template through ```config_generator.py``` even if you want to tinker manually. This way, you ensure that all necessary parameters are set.
Local videos as well as video inputs are supported. For testing, you can use a pre-saved video on your computer during the config generation.
(Note: the video will be processed frame by frame by the program at the max speed your computer can handle, meaning the video might appear to be playing back rapidly or slowly. This is not an issue for the detection mechanism and is by design. If you want to alter this behavior, see the extra notes section.)

After generating your config, it should now be saved to the config/ folder with the name you set. 
If you want to edit or tinker with the config, you can simply edit it here. This is often much faster than re-generating the entire config through the program if you need a small edit.

The last thing you need to do is to run the program using either of the modes shown in the sections below.

### Testing mode:

Default testing mode - printing the output and useful detection statistics straight into the command line for you to view:
```python main.py config/yourconfig.json```

If you want to exit the program early, press the ESC key or CTRL+C while it's running.

You will now have your output, either in the command line or in a newly generated file in out/. 


### Deployment mode:
Deployment mode is the exact same as testing mode with an added flag.
```python main.py config/yourconfig.json -d```

Deployment mode will run continuously until killed or the saved video ends. The output will be stored in *runs/out.csv*. RPM estimates will only be saved when a new one is calculated.


## Extra notes:
if you want to alter the playback speed, open the main.py file in any editor. Find this line:
k = cv.waitKey(1) & 0xFF

You can change the value in the parenthesis to your liking. Below are some examples:
Very fast (1000fps, but most likely capped by your system):
k = cv.waitKey(1) & 0xFF

Normal (approx. 60fps):
k = cv.waitKey(17) & 0xFF

Slow (20fps):
k = cv.waitKey(50) & 0xFF
