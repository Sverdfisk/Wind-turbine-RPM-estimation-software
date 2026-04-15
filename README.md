# Visual Monitoring System for Wind Turbine RPM Estimation

<div align="center">
  <img src="https://github.com/user-attachments/assets/13daa100-4f05-4031-8455-4026d1b17e54" 
       style="width: 100%; height: auto;" 
       alt="Kamera" />
  <div style="width: 100%; text-align: center;">
    <em>Fully assembled system featuring the custom IMX385LQR image sensor PCB integrated with a Raspberry Pi 5</em>
  </div>
</div>


## Thesis:
"Operators monitoring noise from wind turbines often lack direct access to the turbines’ rotational speed (RPM) data. This master’s thesis aims to address that issue using Sony's IMX385LQR image sensor. 
The research will involve examining possible hardware configurations and exploring software techniques such as image processing. The project will culminate in a proof-of-concept with the goal of developing a prototype capable of monitoring the rotation of wind turbines and reporting their RPM over a given time interval."


## Intro
This repository provides RPM estimation software, Altium files for a custom PCB for the IMX385, and driver files. The driver files are for a Raspberry Pi 5 and works as a compatability layer for the image sensor to work properly. Each component of the project can be used on its own if desired. This means that the custom PCB, driver, or RPM detection software can be used without necessarily depending on the other modules.


### Notes and issues:
- The image pipeline (V4L2 pipeline) is not automatically set up, meaning that manual effort is required to fetch and encode frames. The ```driver/``` folder provides some helpful scripts, but is not a complete configuration. The sensor can still send images to the Pi 5 as pixel data with no formatting.


## PCB Stackup and Layout
The 4-layer PCB was manufactured using the JLC04161H-7628 stackup with a total thickness of 1.6 mm, the 7628 fiberglass weave pattern, and FR-4 TG155 substrate material. It has mounting holes spaced 58 mm × 49 mm apart, measured center-to center allowing it to be mounted directly on the Pi 5 using standoffs.

The exact components used on the assembled PCB can be seen in the BOM included in the output files of the Altium folder as well as the schematics.

<div align="center">
  <div style="width: 100%; max-width: 1000px; margin-bottom: 10px;">
    <em>Color legend used for identifying the net groups on the PCB’s layers as shown in subsequent figures</em>
  </div>
  <img src="https://github.com/user-attachments/assets/f0efd245-8abe-4753-8238-49764ab0f19e" 
       style="width: 100%; height: auto; max-width: 1000px;" 
       alt="PCB Net Group Legend" />
</div>

<br>

<div align="center">
  <table style="width: 100%; max-width: 1000px; border: none; border-collapse: collapse; border-spacing: 0; background-color: #000000; table-layout: fixed;">
    <tr>
      <td align="center" style="width: 50%; border: none; padding: 5px; vertical-align: bottom;">
        <img src="https://github.com/user-attachments/assets/b9db1172-7349-4a67-b895-6acf8f623b2c" style="width: 100%; display: block;" alt="PCB_L1" />
        <em style="display: block; padding-top: 5px; color: #ffffff;">Layer 1 (Top)</em>
      </td>
      <td align="center" style="width: 50%; border: none; padding: 5px; vertical-align: bottom;">
        <img src="https://github.com/user-attachments/assets/9b989b72-a488-4b0d-910d-5705331d76dc" style="width: 100%; display: block;" alt="PCB_L2" />
        <em style="display: block; padding-top: 5px; color: #ffffff;">Layer 2</em>
      </td>
    </tr>
    <tr>
      <td align="center" style="width: 50%; border: none; padding: 5px; vertical-align: bottom;">
        <img src="https://github.com/user-attachments/assets/cd0a8bc4-81a2-4224-bdec-078c5638fb23" style="width: 100%; display: block;" alt="PCB_L3" />
        <em style="display: block; padding-top: 5px; color: #ffffff;">Layer 3</em>
      </td>
      <td align="center" style="width: 50%; border: none; padding: 5px; vertical-align: bottom;">
        <img src="https://github.com/user-attachments/assets/6812c7c2-a867-4cce-a17b-ba76b7565c52" style="width: 100%; display: block;" alt="PCB_L4" />
        <em style="display: block; padding-top: 5px; color: #ffffff;">Layer 4 (Bottom)</em>
      </td>
    </tr>
    <tr>
      <td align="center" style="width: 50%; border: none; padding: 5px; vertical-align: bottom;">
        <img src="https://github.com/user-attachments/assets/20a1dbb7-2951-4ed7-8588-483da33a3249" style="width: 100%; display: block;" alt="PCBA_Front" />
        <em style="display: block; padding-top: 5px; color: #ffffff;">PCBA (Front)</em>
      </td>
      <td align="center" style="width: 50%; border: none; padding: 5px; vertical-align: bottom;">
        <img src="https://github.com/user-attachments/assets/c052b2f2-cae2-49e3-8634-94cc2f2d6c1b" style="width: 100%; display: block;" alt="PCBA_Back" />
        <em style="display: block; padding-top: 5px; color: #ffffff;">PCBA (Back)</em>
      </td>
    </tr>
  </table>
</div>


## Setting up the hardware
- GPIO pins from the PCB to the Raspberry Pi need to be attached. The driver/ folder contains code to be run on the Pi, enabling the GPIO pins for the sensor in a strict, necessary sequence. See ```driver/imx-on.py``` for pin numbers and names. The GPIO pins used can in some cases be changed. If you need to change these values, ensure that pin compatability is retained by looking at the Pi 5's GPIO pinout.
- Ensure that the FFC is connected correctly on both the Pi and the custom PCB. The FFC pins should be pointing *towards* the PCB itself when connecting the cable, such that they are not visible when looking at the PCB from the top.
- **Important: A small hack-job is required to connect the sequencer correctly. Use the ***SEQ*** test point on the PCB as an input voltage by attaching it to a GPIO pin on the Pi 5. In the default case, the ```imx-on.py``` file assumes it is connected to pin 26. Make sure you change this pin value in ```driver/imx-on.py``` if you choose another pin to connect it to**.


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
if you want to alter the playback speed when viewing a pre-saved video, open the main.py file in any editor. Find this line:
k = cv.waitKey(1) & 0xFF

You can change the value in the parenthesis to your liking. Below are some examples:
Very fast (1000fps, but most likely capped by your system):
k = cv.waitKey(1) & 0xFF

Normal (approx. 60fps):
k = cv.waitKey(17) & 0xFF

Slow (20fps):
k = cv.waitKey(50) & 0xFF


## Sample Images

<div align="center">
  <table style="width: 100%; max-width: 1000px; border: none; border-collapse: collapse; border-spacing: 0; background-color: #000000; table-layout: fixed;">
    <tr>
      <td align="center" style="width: 50%; border: none; padding: 5px; vertical-align: bottom;">
        <img src="https://github.com/user-attachments/assets/e4b35f91-b72d-4c88-9639-b0e069b4f18e" 
             style="width: 100%; display: block; border-radius: 8px;" alt="Final Output" />
        <em style="display: block; padding-top: 5px; color: #ffffff;">Final output after software-level Auto White Balance (AWB)</em>
      </td>
      <td align="center" style="width: 50%; border: none; padding: 5px; vertical-align: bottom;">
        <img src="https://github.com/user-attachments/assets/69617741-b23f-4846-af3a-2af95c2c1e86" 
             style="width: 100%; display: block; border-radius: 8px;" alt="Test-case" />
        <em style="display: block; padding-top: 5px; color: #ffffff;">Simulated RPM estimation testcase</em>
      </td>
    </tr>
    <tr>
      <td align="center" style="width: 50%; border: none; padding: 5px; vertical-align: bottom;">
        <img src="https://github.com/user-attachments/assets/e86a8ee1-0972-4981-a1da-05717af0e044" 
             style="width: 100%; display: block; border-radius: 8px;" alt="Unfiltered Output" />
        <em style="display: block; padding-top: 5px; color: #ffffff;">Unfiltered sensor output</em>
      </td>
      <td align="center" style="width: 50%; border: none; padding: 5px; vertical-align: bottom;">
        <img src="https://github.com/user-attachments/assets/1fb5fa21-e5f3-4dfe-89b9-828a6b9cf7fa" 
             style="width: 100%; display: block; border-radius: 8px;" alt="AWB Output" />
        <em style="display: block; padding-top: 5px; color: #ffffff;">Sensor output through the IR-cut filter prior to correction</em>
      </td>
    </tr>
  </table>
</div>
