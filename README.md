# Visual Monitoring System for Wind Turbine RPM Estimation

### Thesis:
"Operators monitoring noise from wind turbines often lack direct access to the turbines’ rotational speed (RPM) data. This master’s thesis aims to address that issue using Sony's IMX385LQR image sensor. 
The research will involve examining possible hardware configurations and exploring software techniques such as image processing. The project will culminate in a proof-of-concept with the goal of developing a prototype capable of monitoring the rotation of wind turbines and reporting their RPM over a given time interval."

## Usage
The code requires a camera or an input video. The feed path is specified in main.py and the RPM is then calculated.
In the folder, you will find hardware, driver and software folders. The hardware folder has files related to the PCB designs. The driver folder contains a modified driver that needs to be installed on a RaspberryPi for the hardware to work. The software folder contains the software needed for detection.

Read "Initial setup" first. If you are deploying the system, read "Real setup". If you are testing, modifying or configuring project parameters, read "Test setup".

### Initial setup
1. Clone the project
2. Enter the software folder
In this folder, you will see everything that is needed if you are simulating a video feed or if you are configurating the project.
The config_generator.py file is an application with a GUI that allows you to generate video feed configs. 
main.py is the main program runner, used to start monitoring RPM.
environment.txt is a conda environment file.

**If you are using your own custom environment:**
Look for environment.yml or requirements.txt. Download the required modules using the module manager of your choice (such as pip). 

**If you are using Conda:** 
Conda can read the environment.yml file. Run the following command:
conda env create -f environment.yml


To start, the program needs some parameters to start detection such as where to look for a video stream. This can all be done through config_generator.py, through manual tinkering, or both. It's recommended to first generate a template through config_generator.py even if you want to tinker manually. This way, you ensure that all necessary parameters are set.
Local videos as well as video inputs are supported. For testing, you can use a pre-saved video on your computer during the config generation.
(Note: the video will be processed frame by frame by the program at the max speed your computer can handle, meaning the video might appear to be playing back rapidly or slowly. This is not an issue for the detection mechanism and is by design. If you want to alter this behavior, see the extra notes section.)

After generating your config, it should now be saved to the config/ folder with the name you set. 
If you want to edit or tinker with the config, you can simply edit it here. This is often much faster than re-generating the entire config through the program if you need a small edit.

The last thing you need to do is to run the program.


### Testing mode:

Default testing mode - printing the output and useful detection statistics straight into the command line for you to view:
*python main.py config/yourconfig.json*

If you want to exit the program early, press the ESC key or CTRL+C while it's running.

You will now have your output, either in the command line or in a newly generated file in out/. 


### Deployment mode:
Deployment mode is the exact same as testing mode with an added flag.
*python main.py config/yourconfig.json -d*

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
