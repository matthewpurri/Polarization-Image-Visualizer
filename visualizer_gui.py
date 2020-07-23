import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from tkinter import *
from tkinter import filedialog

import os
import pickle
import numpy as np
from glob import glob
from copy import deepcopy
from PIL import ImageTk, Image

class Application():
    def __init__(self, root):
        self.root = root
        root.title('Visualizer')

        # Initize some values
        self.image_paths = ['./mask_img.png']
        self.img_num = 0
        self.img_size = (376, 251)
        self.date = '02/20/2000'
        self.times = ['04:15 PM']
        self.x0, self.y0 = None, None
        self.x0_old, self.y0_old = None, None
        self.phase_mode = False
        self.cmap = plt.get_cmap('viridis')
        self.radius = 5  # value for phase hist larger box
        self.n_bins = 100
        self.point_circle = None

        # Init UI
        self.init_gui()

    def init_gui(self):
        self.root.geometry('1000x500')

        # Menu dropdown
        main_menu = Menu(self.root)
        fileMenu = Menu(main_menu)
        main_menu.add_cascade(label='File', menu=fileMenu)
        fileMenu.add_command(label='Open', command=self.open_img_session)
        fileMenu.add_separator()
        fileMenu.add_command(label='Exit', command=self._quit)
        self.root.config(menu=main_menu)

        # Add exit button
        exitButton = Button(self.root, text='EXIT', command=self._quit)
        exitButton.grid(row=2, column=1)

        # Image viewer frame
        self.imgViewFrame = LabelFrame(self.root, text='image viewer', padx=50, pady=50)
        self.imgViewFrame.grid(row=0, column=0, rowspan=2)

        backImgButton = Button(self.imgViewFrame, text='<<', command=lambda: self.update_image(-1))
        nextImgButton = Button(self.imgViewFrame, text='>>', command=lambda: self.update_image(1))

        img = ImageTk.PhotoImage(Image.open(self.image_paths[0]).resize(self.img_size))
        self.imgCanvas = Canvas(self.imgViewFrame, width=self.img_size[0], height=self.img_size[1], bg='black')
        self.imgCanvas.grid(row=0, column=0, columnspan=50, rowspan=4)
        viewImg = self.imgCanvas.create_image(0, 0, anchor=NW, image=img)
        self.imgCanvas.image = img

        self.dateLabel = Label(self.imgViewFrame, text='Date: ')
        self.timeLabel = Label(self.imgViewFrame, text='Time: ')

        backImgButton.grid(row=5, column=46, columnspan=2)
        nextImgButton.grid(row=5, column=48, columnspan=2)
        self.dateLabel.grid(row=5, column=0, columnspan=1)
        self.timeLabel.grid(row=5, column=25, columnspan=1)

        # Matplotlib graph viewer frame
        self.graphViewFrame = LabelFrame(self.root, text='plot viewer:', padx=5, pady=5)
        self.graphViewFrame.grid(row=0, column=1)

        self.fig = plt.figure(figsize=(5, 3), dpi=100)
        t = np.arange(0, 3, .01)
        self.ax = self.fig.add_subplot(111)
        self.ax.plot(t, 2 * np.sin(2 * np.pi * t))
        self.plotCanvas = FigureCanvasTkAgg(self.fig, master=self.graphViewFrame)
        self.plotCanvas.draw()
        self.plotCanvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)
        # self.graphViewFrame.bind("<Button 1>", self.update_plot)

        # Options frame
        self.optionFrame = LabelFrame(self.root, text='options:', padx=5, pady=5)
        self.optionFrame.grid(row=1, column=1)

        ## Interactive mode
        Label(self.optionFrame, text='Iteraction: ', justify=LEFT).grid(row=0, column=0, sticky='w', columnspan=5)
        self.interactMode = IntVar()
        self.interactMode.set(0)
        self.interact_mode = 'sine-plot'
        sineRadioOpt = Radiobutton(self.optionFrame, text='Sinusoid', variable=self.interactMode, 
                                   value=0, command=lambda: self.update_interact_mode(self.interactMode.get()))
        phaseRadioOpt = Radiobutton(self.optionFrame, text='Phase Hist', variable=self.interactMode, 
                                    value=1, command=lambda: self.update_interact_mode(self.interactMode.get()))

        sineRadioOpt.grid(row=0, column=5, columnspan=5)
        phaseRadioOpt.grid(row=0, column=10, columnspan=5)

        ## Display image mode
        Label(self.optionFrame, text='Img display: ', justify=LEFT).grid(row=1, column=0, sticky='w', columnspan=5)
        self.imgDisplayMode = IntVar()
        self.imgDisplayMode.set(0)
        maskModeOpt = Radiobutton(self.optionFrame, text='Mask', variable=self.imgDisplayMode, 
                                   value=0, command=lambda: self.update_image_display_type(self.imgDisplayMode.get()))
        rgbModeOpt = Radiobutton(self.optionFrame, text='RGB', variable=self.imgDisplayMode, 
                                   value=1, command=lambda: self.update_image_display_type(self.imgDisplayMode.get()))
        phaseModeOpt = Radiobutton(self.optionFrame, text='Phase Angle', variable=self.imgDisplayMode, 
                                    value=2, command=lambda: self.update_image_display_type(self.imgDisplayMode.get()))
        errorModeOpt = Radiobutton(self.optionFrame, text='Error Image', variable=self.imgDisplayMode, 
                                    value=3, command=lambda: self.update_image_display_type(self.imgDisplayMode.get()))

        maskModeOpt.grid(row=1, column=5, columnspan=5)
        rgbModeOpt.grid(row=1, column=10, columnspan=5)
        phaseModeOpt.grid(row=1, column=15, columnspan=5)
        errorModeOpt.grid(row=1, column=20, columnspan=5)

        ## Drawing mode
        Label(self.optionFrame, text='Drawing Mode: ', justify=LEFT).grid(row=2, column=0, sticky='w', columnspan=5)
        self.drawingMode = IntVar()
        self.drawingMode.set(0)
        rectRadioOpt = Radiobutton(self.optionFrame, text='Rectangle', variable=self.drawingMode, 
                                   value=0, command=lambda: self.update_drawing_type(self.drawingMode.get()))
        lineRadioOpt = Radiobutton(self.optionFrame, text='Line', variable=self.drawingMode, 
                                   value=1, command=lambda: self.update_drawing_type(self.drawingMode.get()))

        rectRadioOpt.grid(row=2, column=5, columnspan=5)
        lineRadioOpt.grid(row=2, column=10, columnspan=5)

    def open_img_session(self):
        img_dir = filedialog.askdirectory(initialdir = "/Users/purri/Documents/Projects/Polarization/images/", title = "Select dir")
        chkpt_dir = os.path.join(img_dir, 'checkpoints')
        self.img_session_dirs = sorted(glob(chkpt_dir + '/*/'))

        # check if a valid directory
        time_path = os.path.join(img_dir, 'times.txt')
        if not os.path.isfile(time_path):
            print('FATAL: No time file available.')
            self._quit()
        if not os.path.isdir(os.path.join(img_dir, 'images')):
            print('FATAL: subdirectory "images" was not found.')
            exit()

        # Load time and date information
        self.times = []
        with open(time_path, 'r') as f:
            for i, line in enumerate(f.readlines()):
                if i == 0:
                    # Date
                    self.date = line.split('\n')[0]
                else:
                    self.times.append(line.split('\n')[0])

        # load sinusoid fit parameters
        self.load_sine_fit_parameters()

        # load images and initialize GUI
        self.update_image_display_type(self.imgDisplayMode.get())

        # Enable events
        self.imgCanvas.bind("<Button 1>", self.update_plot)
        self.root.bind("<Left>", self.update_image_and_plot_left)
        self.root.bind("<Right>", self.update_image_and_plot_right)

    def load_sine_fit_parameters(self):
        self.sine_fits = []
        self.raw_data = []
        self.phase_images = []
        for sess_dir in self.img_session_dirs:
            p_data_path = os.path.join(sess_dir, 'raw_data.p')
            raw_data = pickle.load(open(p_data_path, 'rb'))
            self.raw_data.append(raw_data)
            self.sine_fits.append(raw_data['fit_data'])
            self.phase_images.append(raw_data['phase_img'])

    def load_display_images(self, mode):
        
        if mode == 'rgb':
            image_type = 'align_img.png'
        elif mode == 'mask':
            image_type = 'mask_img.png'
        elif mode == 'phase':
            image_type = 'phase_img.png'
        elif mode == 'fit_error':
            image_type = 'fit_error.png'
        else:
            print('Invalid image type value: "{}"'.format(mode))
            self._quit()

        if mode == 'phase':
            self.add_phase_rotator()
        else:
            self.delete_phase_rotator()

        self.image_paths = [os.path.join(sess_dir, image_type) for sess_dir in self.img_session_dirs]
        self.images = [ImageTk.PhotoImage(Image.open(img_path)) for img_path in self.image_paths]
        self.img_num = 0
        self.update_image(0)

    def update_image(self, inc):
        if len(self.image_paths) == 1:
            return None

        self.img_num += inc

        # Wrap around to the last image
        if self.img_num < 0:
            self.img_num = len(self.image_paths)-1
        elif self.img_num > len(self.image_paths)-1:
            self.img_num = 0

        # Remove the previous image
        self.imgCanvas.grid_forget()

        # Update the image with the selected image
        if self.phase_mode:
            og_img = self.raw_data[self.img_num]['phase_img']
            img = deepcopy(og_img)
            x, y = np.where((img == 0))
            update_val = float(self.phaseSpinbox.get())
            update_val %= 0.9
            img += float(self.phaseSpinbox.get())
            img %= 1
            img[x,y] = 0
            heat_phase_img = self.cmap(img)[:,:,:3]
            img = ImageTk.PhotoImage(Image.fromarray((heat_phase_img*255).astype(np.uint8)))
        else:
            img = ImageTk.PhotoImage(Image.open(self.image_paths[self.img_num]).resize(self.img_size))
        self.imgCanvas = Canvas(self.imgViewFrame, width=self.img_size[0], height=self.img_size[1], bg='black')
        self.imgCanvas.grid(row=0, column=0, columnspan=50, rowspan=4)
        viewImg = self.imgCanvas.create_image(0, 0, anchor=NW, image=img)
        self.imgCanvas.image = img
        self.imgCanvas.bind("<Button 1>", self.update_plot)

        # Update the date and time
        self.dateLabel.config(text='Date: {}'.format(self.date))
        self.timeLabel.config(text='Time: {}'.format(self.times[self.img_num]))

    def update_interact_mode(self, val):
        if val == 0:
            # Sinusoid mode
            self.interact_mode = 'sine-plot'
            self.redraw_sine_fit(self.x0, self.y0)
        elif val == 1:
            # Phase Hist mode
            # https://stackoverflow.com/questions/29789554/tkinter-draw-rectangle-using-a-mouse
            self.interact_mode = 'phase-hist'
            self.redraw_phase_hist(self.x0, self.y0)
        else:
            print('Invalid interaction mode value "{}"'.format(val))
            self._quit()
    
    def update_image_display_type(self, val):
        if val == 0:
            self.load_display_images('mask')
        elif val == 1:
            self.load_display_images('rgb')
        elif val == 2:
            self.load_display_images('phase')
        elif val == 3:
            self.load_display_images('fit_error')
        else:
            print('Invalid image display mode value "{}"'.format(val))
            self._quit()

    def update_drawing_type(self, val):
        if val == 0:
            # TODO Rectangle drawing mode
            print('Sinusiod mode')
        elif val == 1:
            # TODO Line drawing mode
            print('Phase histogram mode')
        else:
            print('Invalid drawing mode value "{}"'.format(val))
            self._quit()

    def update_plot(self, event):
        if not self.x0 is None: 
            self.x0_old = 0
        else:
            self.x0_old = self.x0

        if not self.y0 is None: 
            self.y0_old = 0
        else:
            self.y0_old = self.y0

        x0 = int(event.y)  # Event swaps x and y
        y0 = int(event.x)

        # print('Click registered: {}, {}'.format(x0, y0))
        self.x0, self.y0 = x0, y0

        try:
            if self.interact_mode == 'sine-plot':
                self.redraw_sine_fit(x0, y0)
            elif self.interact_mode == 'phase-hist':
                self.redraw_phase_hist(x0, y0)
        except KeyError:
            self.x0, self.y0 = self.x0_old, self.y0_old
            print('Click out of bounds: {}, {}'.format(x0, y0))

    def redraw_sine_fit(self, x0, y0):
        # Get plot values
        sine_fit = self.sine_fits[self.img_num]
        angles = sine_fit[x0, y0]['angles']
        fit_vals = sine_fit[x0, y0]['fit_values']
        real_vals = sine_fit[x0, y0]['real_values']

        # Redraw plot
        self.ax.clear()
        self.ax.plot(angles, fit_vals, '*b-')
        self.ax.plot(angles, real_vals, '*r-')
        self.ax.set_ylim((-50, 50))
        self.plotCanvas.draw()
        self.create_circle()

    def redraw_phase_hist(self, x0, y0):
        # get phase hist values
        phase_img = self.phase_images[self.img_num]
        phase_vals = phase_img[x0-self.radius:x0+self.radius,y0-self.radius:y0+self.radius]

        # redraw phase histogram
        hist, edges = np.histogram(phase_vals, bins=self.n_bins, range=[0, np.pi+1e-6])
        hist[0] = 0  # zero-out blank pixels
        self.ax.clear()
        self.ax.bar(edges, np.roll(np.append(hist, [0]), 1), width=edges[1])
        self.plotCanvas.draw()
        self.create_circle()

    def update_image_and_plot_left(self, event):
        # print('Left clicked!')
        self.update_image(-1)
        if self.interact_mode == 'sine-plot':
            self.redraw_sine_fit(self.x0, self.y0)
        elif self.interact_mode == 'phase-hist': 
            self.redraw_phase_hist(self.x0, self.y0)
        self.create_circle()

    def update_image_and_plot_right(self, event):
        # print('Right clicked!')
        self.update_image(1)
        if self.interact_mode == 'sine-plot':
            self.redraw_sine_fit(self.x0, self.y0)
        elif self.interact_mode == 'phase-hist': 
            self.redraw_phase_hist(self.x0, self.y0)

    def _quit(self):
        self.root.quit()     # stops mainloop
        self.root.destroy()  # this is necessary on Windows to prevent
                        # Fatal Python Error: PyEval_RestoreThread: NULL tstate

    def add_phase_rotator(self):
        self.phase_mode = True
        values = [i/10 for i in range(10)]
        self.phaseSpinbox = Spinbox(self.imgViewFrame, values=values, wrap=False, command=lambda: self.update_image(0))
        self.phaseSpinbox.grid(row=6, column=46, columnspan=4)

    def delete_phase_rotator(self):
        try:
            self.phase_mode = False
            self.phaseSpinbox.grid_forget()
        except AttributeError:
            pass

    def create_circle(self): #center coordinates, radius
        if not self.point_circle is None:
            self.imgCanvas.delete(self.point_circle)

        x0 = self.y0 - self.radius
        y0 = self.x0 - self.radius
        x1 = self.y0 + self.radius
        y1 = self.x0 + self.radius
        self.point_circle = self.imgCanvas.create_oval(x0, y0, x1, y1, fill="green")

if __name__ == '__main__':
    root = Tk()

    app = Application(root)

    root.mainloop()

    