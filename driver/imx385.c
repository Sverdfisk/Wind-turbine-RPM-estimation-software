// SPDX-License-Identifier: GPL-2.0
/*
 * Sony IMX385 CMOS Image Sensor Driver
 *
 * Copyright (C) 2019 FRAMOS GmbH.
 *
 * Copyright (C) 2019 Linaro Ltd.
 * Author: Manivannan Sadhasivam <manivannan.sadhasivam@linaro.org>
 */

#include <linux/clk.h>
#include <linux/delay.h>
#include <linux/gpio/consumer.h>
#include <linux/i2c.h>
#include <linux/module.h>
#include <linux/pm_runtime.h>
#include <linux/regmap.h>
#include <linux/regulator/consumer.h>
#include <linux/version.h>
#include <media/media-entity.h>
#include <media/v4l2-ctrls.h>
#include <media/v4l2-device.h>
#include <media/v4l2-fwnode.h>
#include <media/v4l2-subdev.h>

#define IMX385_STANDBY 0x3000 //
#define IMX385_REGHOLD 0x3001//
#define IMX385_XMSTA 0x3002//
#define IMX385_RESET 0x3003//
#define IMX385_FR_FDG_SEL 0x3009//
#define IMX385_BLKLEVEL_LOW 0x300a//
#define IMX385_BLKLEVEL_HIGH 0x300b//
#define IMX385_GAIN 0x3014//
#define IMX385_EXPOSURE_MIN 1
#define IMX385_EXPOSURE_STEP 1
#define IMX385_EXPOSURE_LOW 0x3020
#define IMX385_VMAX_LOW 0x3018
#define IMX385_VMAX_MAX 0x1ffff
#define IMX385_HMAX_LOW 0x301b //0x301c
#define IMX385_HMAX_HIGH 0x301c //0x301d
#define IMX385_HMAX_MIN 2200 
#define IMX385_HMAX_MAX 0x3fff
#define IMX385_PGCTRL 0x308c// overlaps with gain
#define IMX385_PHY_LANE_NUM 0x3346 // 0x3407
#define IMX385_CSI_LANE_MODE 0x337F// 0x3443

#define IMX385_PGCTRL_REGEN BIT(0)
#define IMX385_PGCTRL_THRU BIT(1)
#define IMX385_PGCTRL_MODE(n) ((n) << 4)

/* IMX385 native and active pixel array size. */
#define IMX385_NATIVE_WIDTH			1952U
#define IMX385_NATIVE_HEIGHT		1113U
#define IMX385_PIXEL_ARRAY_LEFT		16U
#define IMX385_PIXEL_ARRAY_TOP		8U
#define IMX385_PIXEL_ARRAY_WIDTH	1920U
#define IMX385_PIXEL_ARRAY_HEIGHT	1080U


static const char * const imx385_supply_name[] = {
	"vdda",
	"vddd",
	"vdddo",
};

#define IMX385_NUM_SUPPLIES ARRAY_SIZE(imx385_supply_name)

struct imx385_regval {
	u16 reg;
	u8 val;
};

struct imx385_mode {
	u32 width;
	u32 height;
	u32 hmax;
	u32 vmax;
	u8 link_freq_index;

	struct v4l2_rect crop;

	const struct imx385_regval *data;
	u32 data_size;
};

struct imx385 {
	struct device *dev;
	struct clk *xclk;
	struct regmap *regmap;
	u8 nlanes;
	u8 bpp;
	u16 hmax_min;

	struct v4l2_subdev sd;
	struct media_pad pad;
	struct v4l2_mbus_framefmt current_format;
	const struct imx385_mode *current_mode;

	struct regulator_bulk_data supplies[IMX385_NUM_SUPPLIES];

	struct v4l2_ctrl_handler ctrls;
	struct v4l2_ctrl *link_freq;
	struct v4l2_ctrl *pixel_rate;
	struct v4l2_ctrl *hblank;
	struct v4l2_ctrl *vblank;
	struct v4l2_ctrl *exposure;
	struct v4l2_ctrl *analog_gain;
	struct v4l2_ctrl *digital_gain;

	struct mutex lock;
};

struct imx385_pixfmt {
	u32 code;
	u8 bpp;
};

static const struct imx385_pixfmt imx385_formats[] = {
	{ MEDIA_BUS_FMT_SRGGB10_1X10, 10 },
};

static const struct regmap_config imx385_regmap_config = {
	.reg_bits = 16,
	.val_bits = 8,
	.cache_type = REGCACHE_RBTREE,
};

static const char * const imx385_test_pattern_menu[] = {
	"Disabled",
	"Sequence Pattern 1",
	"Horizontal Color-bar Chart",
	"Vertical Color-bar Chart",
	"Sequence Pattern 2",
	"Gradation Pattern 1",
	"Gradation Pattern 2",
	"000/555h Toggle Pattern",
};

static const struct imx385_regval imx385_10bit_settings[] = {
	{ 0x3005, 0x00 },
	{ 0x337d, 0x0A },
	{ 0x337e, 0x0A },

	/* INCK Settings */
	{ 0x305c, 0x28 },
	{ 0x305d, 0x00 },
	{ 0x305e, 0x20 },
	{ 0x305f, 0x00 },

	/* Black level */
	{ 0x300a, 0x3C },
	{ 0x300b, 0x00 },

	/* Global Timings */
	{ 0x3382, 0x5f },
	{ 0x3383, 0x1f },
	{ 0x3384, 0x37 },
	{ 0x3385, 0x1f },
	{ 0x3386, 0x17 },
	{ 0x3387, 0x17 },
	{ 0x3388, 0x67 },
	{ 0x3389, 0x27 },

	{ 0x336b, 0x37 },

	{ 0x3344, 0x20 },

};

static const struct imx385_regval imx385_12bit_settings[] = {
	{ 0x3005, 0x01 },
	{ 0x337d, 0x0C },
	{ 0x337e, 0x0C },

	/* INCK Settings */
	{ 0x305c, 0x18 },
	{ 0x305d, 0x00 },
	{ 0x305e, 0x20 },
	{ 0x305f, 0x00 },

	/* Black level */
	{ 0x300a, 0xF0 },
	{ 0x300b, 0x00 },

	/* Global Timings */
	{ 0x3382, 0x67 },
	{ 0x3383, 0x1f },
	{ 0x3384, 0x3f },
	{ 0x3385, 0x27 },
	{ 0x3386, 0x1f },
	{ 0x3387, 0x17 },
	{ 0x3388, 0x77 },
	{ 0x3389, 0x27 },

	{ 0x336b, 0x3f },

	{ 0x3344, 0x20 },

};

static const struct imx385_regval imx385_1080p30_settings[] = {
	{ 0x3007, 0x00 }, 
	{ 0x3009, 0x02 },
	{ 0x3012, 0x2c },
	{ 0x3013, 0x01 },
	{ 0x3014, 0x07 }, //Gain
	{ 0x3018, 0x46 }, // Default value is for 30 fps.
	{ 0x3019, 0x05 },
	{ 0x301b, 0x30 },
	{ 0x301c, 0x11 },
	{ 0x3020, 0x02 }, //SHS1
	{ 0x3021, 0x00 }, //SHS1
	{ 0x3044, 0x01 },
	{ 0x3046, 0x30 },
	{ 0x3047, 0x38 },
	{ 0x3049, 0x0a },
	{ 0x3054, 0x66 },
	{ 0x310b, 0x07 },
	{ 0x3110, 0x12 },
	{ 0x31ed, 0x38 },
	{ 0x3338, 0xd4 },
	{ 0x3339, 0x40 },
	{ 0x333a, 0x10 },
	{ 0x333b, 0x00 },
	{ 0x333c, 0xd4 },
	{ 0x333d, 0x40 },
	{ 0x333e, 0x10 },
	{ 0x333f, 0x00 },
	{ 0x336c, 0x1f },

	/* INCK FREQ1 */
	{ 0x3380, 0x20 },
	{ 0x3381, 0x25 },


	/* INCK FREQ2 */
	{ 0x338d, 0xb4 },
	{ 0x338e, 0x01 },

	/* WINPH */
	{ 0x303c, 0x0C },
	{ 0x303d, 0x00 },

	/* WINWH */
	{ 0x303e, 0x80 },
	{ 0x303f, 0x07 },

	/* WINPV */
	{ 0x3038,  0x08 },
	{ 0x3039,  0x00 },

	/* WINWV */
	{ 0x303A, 0x38 },
	{ 0x303B, 0x04 },

	/* PIC_SIZE_V */
	{ 0x3057, 0x38 },
	{ 0x3058, 0x04 },
};

/* supported link frequencies */
#define FREQ_INDEX_1080P	0
#define FREQ_INDEX_720P		1
static const s64 imx385_link_freq_2lanes[] = {
	[FREQ_INDEX_1080P] = 371250000,
	[FREQ_INDEX_720P] = 297000000,
};
static const s64 imx385_link_freq_4lanes[] = {
	[FREQ_INDEX_1080P] = 185625000,
	[FREQ_INDEX_720P] = 148500000,
};

/*
 * In this function and in the similar ones below We rely on imx385_probe()
 * to ensure that nlanes is either 2 or 4.
 */
static inline const s64 *imx385_link_freqs_ptr(const struct imx385 *imx385)
{
	if (imx385->nlanes == 2)
		return imx385_link_freq_2lanes;
	else
		return imx385_link_freq_4lanes;
}

static inline int imx385_link_freqs_num(const struct imx385 *imx385)
{
	if (imx385->nlanes == 2)
		return ARRAY_SIZE(imx385_link_freq_2lanes);
	else
		return ARRAY_SIZE(imx385_link_freq_4lanes);
}

/* Mode configs */
static const struct imx385_mode imx385_modes_2lanes[] = {
	{
		.width = 1920,
		.height = 1080,
		.hmax = 0x1130,
		.vmax = 0x0465,
		.crop = {
			.left = 16,
			.top = 9,
			.width = 1920,
			.height = 1080
		},
		.link_freq_index = FREQ_INDEX_1080P,
		.data = imx385_1080p30_settings,
		.data_size = ARRAY_SIZE(imx385_1080p30_settings),
	},
};

static const struct imx385_mode imx385_modes_4lanes[] = {
	{
		.width = 1920,
		.height = 1080,
		.hmax = 0x1130,
		.vmax = 0x0465,
		.crop = {
			.left = 16,
			.top = 9,
			.width = 1920,
			.height = 1080
		},
		.link_freq_index = FREQ_INDEX_1080P,
		.data = imx385_1080p30_settings,
		.data_size = ARRAY_SIZE(imx385_1080p30_settings),
	},
};

static inline const struct imx385_mode *imx385_modes_ptr(const struct imx385 *imx385)
{
	if (imx385->nlanes == 2)
		return imx385_modes_2lanes;
	else
		return imx385_modes_4lanes;
}

static inline int imx385_modes_num(const struct imx385 *imx385)
{
	if (imx385->nlanes == 2)
		return ARRAY_SIZE(imx385_modes_2lanes);
	else
		return ARRAY_SIZE(imx385_modes_4lanes);
}

static inline struct imx385 *to_imx385(struct v4l2_subdev *_sd)
{
	return container_of(_sd, struct imx385, sd);
}

static inline int imx385_read_reg(struct imx385 *imx385, u16 addr, u8 *value)
{
	unsigned int regval;
	int ret;

	ret = regmap_read(imx385->regmap, addr, &regval);
	if (ret) {
		dev_err(imx385->dev, "I2C read failed for addr: %x\n", addr);
		return ret;
	}

	*value = regval & 0xff;

	return 0;
}

static int imx385_write_reg(struct imx385 *imx385, u16 addr, u8 value)
{
	int ret;

	ret = regmap_write(imx385->regmap, addr, value);
	dev_info(imx385->dev, "I2C write_reg: ADDR=%x | VALUE=%x", addr, value);

	if (ret) {
		dev_err(imx385->dev, "I2C write failed for addr: %x\n", addr);
		return ret;
	}

	return ret;
}

static int imx385_set_register_array(struct imx385 *imx385,
				     const struct imx385_regval *settings,
				     unsigned int num_settings)
{
	unsigned int i;
	int ret;

	for (i = 0; i < num_settings; ++i, ++settings) {
		ret = imx385_write_reg(imx385, settings->reg, settings->val);
		if (ret < 0)
			return ret;
	}

	/* Provide 10ms settle time */
	usleep_range(10000, 11000);

	return 0;
}

static int imx385_write_buffered_reg(struct imx385 *imx385, u16 address_low,
				     u8 nr_regs, u32 value)
{
	unsigned int i;
	int ret;

	ret = imx385_write_reg(imx385, IMX385_REGHOLD, 0x01);
	if (ret) {
		dev_err(imx385->dev, "Error setting hold register\n");
		return ret;
	}

	for (i = 0; i < nr_regs; i++) {
		ret = imx385_write_reg(imx385, address_low + i,
				       (u8)(value >> (i * 8)));
		if (ret) {
			dev_err(imx385->dev, "Error writing buffered registers\n");
			return ret;
		}
	}

	ret = imx385_write_reg(imx385, IMX385_REGHOLD, 0x00);
	if (ret) {
		dev_err(imx385->dev, "Error setting hold register\n");
		return ret;
	}

	return ret;
}

static int imx385_set_gain(struct imx385 *imx385)
{
	int ret;
	u32 value = imx385->analog_gain->val + imx385->digital_gain->val;

	ret = imx385_write_buffered_reg(imx385, IMX385_GAIN, 2, value);
	if (ret)
		dev_err(imx385->dev, "Unable to write gain\n");

	return ret;
}

static int imx385_set_exposure(struct imx385 *imx385, u32 value)
{
	u32 exposure = (imx385->current_mode->height + imx385->vblank->val) -
						value - 1;
	int ret;

	ret = imx385_write_buffered_reg(imx385, IMX385_EXPOSURE_LOW, 3,
					exposure);
	if (ret)
		dev_err(imx385->dev, "Unable to write exposure\n");

	return ret;
}

static int imx385_set_hmax(struct imx385 *imx385, u32 val)
{
	int ret;

	ret = imx385_write_reg(imx385, IMX385_HMAX_LOW, (val & 0xff));
	if (ret) {
		dev_err(imx385->dev, "Error setting HMAX register\n");
		return ret;
	}

	ret = imx385_write_reg(imx385, IMX385_HMAX_HIGH, ((val >> 8) & 0xff));
	if (ret) {
		dev_err(imx385->dev, "Error setting HMAX register\n");
		return ret;
	}

	return 0;
}


static int imx385_set_vmax(struct imx385 *imx385, u32 val)
{
	u32 vmax = val + imx385->current_mode->height;
	int ret;

	ret = imx385_write_buffered_reg(imx385, IMX385_VMAX_LOW, 3,
					vmax);
	if (ret)
		dev_err(imx385->dev, "Unable to write vmax\n");

	/*
	 * Changing vblank changes the allowed range for exposure.
	 * We don't supply the current exposure as default here as it
	 * may lie outside the new range. We will reset it just below.
	 */
	__v4l2_ctrl_modify_range(imx385->exposure,
				 IMX385_EXPOSURE_MIN,
				 vmax - 2,
				 IMX385_EXPOSURE_STEP,
				 vmax - 2);

	/*
	 * Becuse of the way exposure works for this sensor, updating
	 * vblank causes the effective exposure to change, so we must
	 * set it back to the "new" correct value.
	 */
	imx385_set_exposure(imx385, imx385->exposure->val);

	return ret;
}

/* Stop streaming */
static int imx385_stop_streaming(struct imx385 *imx385)
{
	int ret;
	dev_err(imx385->dev, "Stopped streaming");
	ret = imx385_write_reg(imx385, IMX385_STANDBY, 0x01);
	if (ret < 0)
		return ret;

	msleep(30);

	return imx385_write_reg(imx385, IMX385_XMSTA, 0x01);
}

static int imx385_set_ctrl(struct v4l2_ctrl *ctrl)
{
	struct imx385 *imx385 = container_of(ctrl->handler,
					     struct imx385, ctrls);
	int ret = 0;

	/* V4L2 controls values will be applied only when power is already up */
	if (!pm_runtime_get_if_in_use(imx385->dev))
		return 0;

	switch (ctrl->id) {
	case V4L2_CID_ANALOGUE_GAIN:
	case V4L2_CID_GAIN:
		ret = imx385_set_gain(imx385);
		break;
	case V4L2_CID_EXPOSURE:
		ret = imx385_set_exposure(imx385, ctrl->val);
		break;
	case V4L2_CID_HBLANK:
		ret = imx385_set_hmax(imx385, ctrl->val);
		break;
	case V4L2_CID_VBLANK:
		ret = imx385_set_vmax(imx385, ctrl->val);
		break;
	case V4L2_CID_TEST_PATTERN:
		if (ctrl->val) {
			imx385_write_reg(imx385, IMX385_BLKLEVEL_LOW, 0x00);
			imx385_write_reg(imx385, IMX385_BLKLEVEL_HIGH, 0x00);
			usleep_range(10000, 11000);
			imx385_write_reg(imx385, IMX385_PGCTRL,
					 (u8)(IMX385_PGCTRL_REGEN |
					 IMX385_PGCTRL_THRU |
					 IMX385_PGCTRL_MODE(ctrl->val)));
		} else {
			imx385_write_reg(imx385, IMX385_PGCTRL, 0x00);
			usleep_range(10000, 11000);
			if (imx385->bpp == 10)
				imx385_write_reg(imx385, IMX385_BLKLEVEL_LOW,
						 0x3c);
			else /* 12 bits per pixel */
				imx385_write_reg(imx385, IMX385_BLKLEVEL_LOW,
						 0xf0);
			imx385_write_reg(imx385, IMX385_BLKLEVEL_HIGH, 0x00);
		}
		break;
	default:
		ret = -EINVAL;
		break;
	}

	pm_runtime_put(imx385->dev);

	return ret;
}

static const struct v4l2_ctrl_ops imx385_ctrl_ops = {
	.s_ctrl = imx385_set_ctrl,
};

static int imx385_enum_mbus_code(struct v4l2_subdev *sd,
#if LINUX_VERSION_CODE <= KERNEL_VERSION(5,13,0)
			 	 struct v4l2_subdev_pad_config *cfg,
#else
				 struct v4l2_subdev_state *state,
#endif
				 struct v4l2_subdev_mbus_code_enum *code)
{
	if (code->index >= ARRAY_SIZE(imx385_formats))
		return -EINVAL;

	code->code = imx385_formats[code->index].code;

	return 0;
}

static int imx385_enum_frame_size(struct v4l2_subdev *sd,
#if LINUX_VERSION_CODE <= KERNEL_VERSION(5,13,0)
			 	  struct v4l2_subdev_pad_config *cfg,
#else
				  struct v4l2_subdev_state *state,
#endif
				  struct v4l2_subdev_frame_size_enum *fse)
{
	const struct imx385 *imx385 = to_imx385(sd);
	const struct imx385_mode *imx385_modes = imx385_modes_ptr(imx385);

	if ((fse->code != imx385_formats[0].code) &&
	    (fse->code != imx385_formats[1].code))
		return -EINVAL;

	if (fse->index >= imx385_modes_num(imx385))
		return -EINVAL;

	fse->min_width = imx385_modes[fse->index].width;
	fse->max_width = imx385_modes[fse->index].width;
	fse->min_height = imx385_modes[fse->index].height;
	fse->max_height = imx385_modes[fse->index].height;

	return 0;
}

static int imx385_enum_frame_interval(struct v4l2_subdev *sd,
#if LINUX_VERSION_CODE <= KERNEL_VERSION(5,13,0)
				      struct v4l2_subdev_pad_config *cfg,
#else
				      struct v4l2_subdev_state *state,
#endif
				      struct v4l2_subdev_frame_interval_enum *fie)
{
	fie->interval.numerator = 1;
	fie->interval.denominator = 25;

	return 0;
}

static int imx385_get_fmt(struct v4l2_subdev *sd,
#if LINUX_VERSION_CODE <= KERNEL_VERSION(5,13,0)
			  struct v4l2_subdev_pad_config *cfg,
#else
			  struct v4l2_subdev_state *state,
#endif
			  struct v4l2_subdev_format *fmt)
{
	struct imx385 *imx385 = to_imx385(sd);
	struct v4l2_mbus_framefmt *framefmt;

	mutex_lock(&imx385->lock);

	if (fmt->which == V4L2_SUBDEV_FORMAT_TRY)
#if LINUX_VERSION_CODE <= KERNEL_VERSION(5,13,0)
		framefmt = v4l2_subdev_get_try_format(&imx385->sd, cfg,
						      fmt->pad);
#else
		framefmt = v4l2_subdev_state_get_format(state,
						      fmt->pad, 0);
#endif
	else
		framefmt = &imx385->current_format;

	fmt->format = *framefmt;

	mutex_unlock(&imx385->lock);

	return 0;
}

static inline u8 imx385_get_link_freq_index(struct imx385 *imx385)
{
	return imx385->current_mode->link_freq_index;
}

static s64 imx385_get_link_freq(struct imx385 *imx385)
{
	u8 index = imx385_get_link_freq_index(imx385);

	return *(imx385_link_freqs_ptr(imx385) + index);
}

static u64 imx385_calc_pixel_rate(struct imx385 *imx385)
{
	s64 link_freq = imx385_get_link_freq(imx385);
	u8 nlanes = imx385->nlanes;
	u64 pixel_rate;

	/* pixel rate = link_freq * 2 * nr_of_lanes / bits_per_sample */
	pixel_rate = link_freq * 2 * nlanes;
	do_div(pixel_rate, imx385->bpp);
	return pixel_rate;
}

static int imx385_set_fmt(struct v4l2_subdev *sd,
#if LINUX_VERSION_CODE <= KERNEL_VERSION(5,13,0)
			  struct v4l2_subdev_pad_config *cfg,
#else
			  struct v4l2_subdev_state *state,
#endif
			  struct v4l2_subdev_format *fmt)
{
	struct imx385 *imx385 = to_imx385(sd);
	const struct imx385_mode *mode;
	struct v4l2_mbus_framefmt *format;
	unsigned int i;

	mutex_lock(&imx385->lock);

	mode = v4l2_find_nearest_size(imx385_modes_ptr(imx385),
				      imx385_modes_num(imx385), width, height,
				      fmt->format.width, fmt->format.height);
	if (!mode) {       
	    mode = imx385_modes_ptr(imx385);
	}	

	if (fmt->pad) {
	    fmt->pad = 0;
	}

	fmt->format.width = mode->width;
	fmt->format.height = mode->height;

	for (i = 0; i < ARRAY_SIZE(imx385_formats); i++)
		if (imx385_formats[i].code == fmt->format.code)
			break;

	if (i >= ARRAY_SIZE(imx385_formats))
		i = 0;

	fmt->format.code = imx385_formats[i].code;
	fmt->format.field = V4L2_FIELD_NONE;

	if (fmt->which == V4L2_SUBDEV_FORMAT_TRY) {
#if LINUX_VERSION_CODE <= KERNEL_VERSION(5,13,0)
		format = v4l2_subdev_get_try_format(sd, cfg, fmt->pad);
#else
		if (state) {
		    format = v4l2_subdev_state_get_format(state, fmt->pad, 0);
		}
		else {
		    format = &imx385->current_format;
		}

#endif
	} else {
		format = &imx385->current_format;
		imx385->current_mode = mode;
		imx385->bpp = imx385_formats[i].bpp;

		if (imx385->link_freq)
			__v4l2_ctrl_s_ctrl(imx385->link_freq,
					   imx385_get_link_freq_index(imx385));
		if (imx385->pixel_rate)
			__v4l2_ctrl_s_ctrl_int64(imx385->pixel_rate,
						 imx385_calc_pixel_rate(imx385));
	}

	*format = fmt->format;

	mutex_unlock(&imx385->lock);

	return 0;
}

static const struct v4l2_rect *
#if LINUX_VERSION_CODE <= KERNEL_VERSION(5,13,0)
__imx385_get_pad_crop(struct imx385 *imx385, struct v4l2_subdev_pad_config *cfg,
		      unsigned int pad, enum v4l2_subdev_format_whence which)
#else
__imx385_get_pad_crop(struct imx385 *imx385, struct v4l2_subdev_state *state,
		      unsigned int pad, enum v4l2_subdev_format_whence which)
#endif
{
	switch (which) {
	case V4L2_SUBDEV_FORMAT_TRY:
#if LINUX_VERSION_CODE <= KERNEL_VERSION(5,13,0)
		return v4l2_subdev_get_try_crop(&imx385->sd, cfg, pad);
#else
		return v4l2_subdev_state_get_crop(state, pad);
#endif
	case V4L2_SUBDEV_FORMAT_ACTIVE:
		return &imx385->current_mode->crop;
	}

	return NULL;
}

static int imx385_get_selection(struct v4l2_subdev *sd,
#if LINUX_VERSION_CODE <= KERNEL_VERSION(5,13,0)
				struct v4l2_subdev_pad_config *cfg,
#else
				struct v4l2_subdev_state *state,
#endif
				struct v4l2_subdev_selection *sel)
{
	switch (sel->target) {
	case V4L2_SEL_TGT_CROP: {
		struct imx385 *imx385 = to_imx385(sd);

		mutex_lock(&imx385->lock);
#if LINUX_VERSION_CODE <= KERNEL_VERSION(5,13,0)
		sel->r = *__imx385_get_pad_crop(imx385, cfg, sel->pad,
						sel->which);
#else
		sel->r = *__imx385_get_pad_crop(imx385, state, sel->pad,
						sel->which);
#endif
		mutex_unlock(&imx385->lock);

		return 0;
	}

	case V4L2_SEL_TGT_NATIVE_SIZE:
		sel->r.top = 0;
		sel->r.left = 0;
		sel->r.width = IMX385_NATIVE_WIDTH;
		sel->r.height = IMX385_NATIVE_HEIGHT;

		return 0;

	case V4L2_SEL_TGT_CROP_DEFAULT:
	case V4L2_SEL_TGT_CROP_BOUNDS:
		sel->r.top = IMX385_PIXEL_ARRAY_TOP;
		sel->r.left = IMX385_PIXEL_ARRAY_LEFT;
		sel->r.width = IMX385_PIXEL_ARRAY_WIDTH;
		sel->r.height = IMX385_PIXEL_ARRAY_HEIGHT;

		return 0;
	}

	return -EINVAL;
}
static int imx385_entity_init_state(struct v4l2_subdev *subdev,
#if LINUX_VERSION_CODE <= KERNEL_VERSION(5,13,0)
				struct v4l2_subdev_pad_config *cfg)
#else
				struct v4l2_subdev_state *state)
#endif
{
	struct v4l2_subdev_format fmt = { 0 };

#if LINUX_VERSION_CODE <= KERNEL_VERSION(5,13,0)
	fmt.which = cfg ? V4L2_SUBDEV_FORMAT_TRY : V4L2_SUBDEV_FORMAT_ACTIVE;
#else
	fmt.which = state ? V4L2_SUBDEV_FORMAT_TRY : V4L2_SUBDEV_FORMAT_ACTIVE;
#endif
	fmt.format.width = 1920;
	fmt.format.height = 1080;

#if LINUX_VERSION_CODE <= KERNEL_VERSION(5,13,0)
	imx385_set_fmt(subdev, cfg, &fmt);
#else
	imx385_set_fmt(subdev, state, &fmt);
#endif

	return 0;
}

static int imx385_write_current_format(struct imx385 *imx385)
{
	int ret;

	switch (imx385->current_format.code) {
	case MEDIA_BUS_FMT_SRGGB10_1X10:
		ret = imx385_set_register_array(imx385, imx385_10bit_settings,
						ARRAY_SIZE(
							imx385_10bit_settings));

		if (ret < 0) {
			dev_err(imx385->dev, "Could not set format registers\n");
			return ret;
		}
		break;
	}

	return 0;
}

/* Start streaming */
static int imx385_start_streaming(struct imx385 *imx385)
{
	int ret;

	/* Set init register settings */
/*	ret = imx385_set_register_array(imx385, imx385_global_init_settings,
					ARRAY_SIZE(
						imx385_global_init_settings));
	if (ret < 0) {
		dev_err(imx385->dev, "Could not set init registers\n");
		return ret;
	}
*/
	/* Apply default values of current mode */

	dev_err(imx385->dev, "Started streaming");
	ret = imx385_set_register_array(imx385, imx385->current_mode->data,
					imx385->current_mode->data_size);
	if (ret < 0) {
		dev_err(imx385->dev, "Could not set current mode\n");
		return ret;
	}

	/* Apply the register values related to current frame format */
	ret = imx385_write_current_format(imx385);
	if (ret < 0) {
		dev_err(imx385->dev, "Could not set frame format\n");
		return ret;
	}


	ret = imx385_set_hmax(imx385, imx385->current_mode->hmax);
	if (ret < 0)
		return ret;

	/* Apply customized values from user */
	ret = v4l2_ctrl_handler_setup(imx385->sd.ctrl_handler);
	if (ret) {
		dev_err(imx385->dev, "Could not sync v4l2 controls\n");
		return ret;
	}

	ret = imx385_write_reg(imx385, IMX385_STANDBY, 0x00);
	if (ret < 0)
		return ret;

	msleep(30);

	/* Start streaming */
	return imx385_write_reg(imx385, IMX385_XMSTA, 0x00);/* Apply default values of current mode */
}

static int imx385_set_stream(struct v4l2_subdev *sd, int enable)
{
	struct imx385 *imx385 = to_imx385(sd);
	int ret = 0;

	if (enable) {
		ret = pm_runtime_get_sync(imx385->dev);
		if (ret < 0) {
			pm_runtime_put_noidle(imx385->dev);
			goto unlock_and_return;
		}

		ret = imx385_start_streaming(imx385);
		if (ret) {
			dev_err(imx385->dev, "Start stream failed\n");
			pm_runtime_put(imx385->dev);
			goto unlock_and_return;
		}
	} else {
		imx385_stop_streaming(imx385);
		pm_runtime_put(imx385->dev);
	}

unlock_and_return:
	return ret;
}

static int imx385_get_regulators(struct device *dev, struct imx385 *imx385)
{
	unsigned int i;

	for (i = 0; i < IMX385_NUM_SUPPLIES; i++)
		imx385->supplies[i].supply = imx385_supply_name[i];

	return devm_regulator_bulk_get(dev, IMX385_NUM_SUPPLIES,
				       imx385->supplies);
}

static int imx385_set_data_lanes(struct imx385 *imx385)
{
	int ret = 0, laneval, frsel;

	switch (imx385->nlanes) {
	case 2:
		laneval = 0x01;
		frsel = 0x02;
		dev_info(imx385->dev, "Driver set to 2 lane\n");
		break;
	case 4:
		laneval = 0x03;
		frsel = 0x02;
		dev_info(imx385->dev, "Driver set to 4 lane\n");
		break;
	default:
		/*
		 * We should never hit this since the data lane count is
		 * validated in probe itself
		 */
		dev_err(imx385->dev, "Lane configuration not supported\n");
		ret = -EINVAL;
		goto exit;
	}

	ret = imx385_write_reg(imx385, IMX385_PHY_LANE_NUM, laneval);
	if (ret) {
		dev_err(imx385->dev, "Lane number set to %u lanes", imx385->nlanes);
		dev_err(imx385->dev, "Error setting Physical Lane number register\n");
		goto exit;
	}

	ret = imx385_write_reg(imx385, IMX385_CSI_LANE_MODE, laneval);
	if (ret) {
		dev_err(imx385->dev, "Error setting CSI Lane mode register\n");
		goto exit;
	}

	ret = imx385_write_reg(imx385, IMX385_FR_FDG_SEL, frsel);
	if (ret)
		dev_err(imx385->dev, "Error setting FR/FDG SEL register\n");

exit:
	return ret;
}

static int imx385_power_on(struct device *dev)
{
	struct i2c_client *client = to_i2c_client(dev);
	struct v4l2_subdev *sd = i2c_get_clientdata(client);
	struct imx385 *imx385 = to_imx385(sd);
	int ret;

	ret = clk_prepare_enable(imx385->xclk);
	if (ret) {
		dev_err(imx385->dev, "Failed to enable clock\n");
		return ret;
	}

	ret = regulator_bulk_enable(IMX385_NUM_SUPPLIES, imx385->supplies);
	if (ret) {
		dev_err(imx385->dev, "Failed to enable regulators\n");
		clk_disable_unprepare(imx385->xclk);
		return ret;
	}

        usleep_range(10000, 20000);           /* 0.1 s */

        usleep_range(10000, 20000);           /* 0.1 s */

	/* Set data lane count */
	imx385_set_data_lanes(imx385);

	return 0;
}

static int imx385_power_off(struct device *dev)
{
	struct i2c_client *client = to_i2c_client(dev);
	struct v4l2_subdev *sd = i2c_get_clientdata(client);
	struct imx385 *imx385 = to_imx385(sd);

	clk_disable_unprepare(imx385->xclk);
	regulator_bulk_disable(IMX385_NUM_SUPPLIES, imx385->supplies);
	return 0;
}

static const struct dev_pm_ops imx385_pm_ops = {
	SET_RUNTIME_PM_OPS(imx385_power_off, imx385_power_on, NULL)
};

static const struct v4l2_subdev_video_ops imx385_video_ops = {
	.s_stream = imx385_set_stream,
};

static const struct v4l2_subdev_internal_ops imx385_internal_ops = {
	.init_state = imx385_entity_init_state
};

static const struct v4l2_subdev_pad_ops imx385_pad_ops = {
	.enum_mbus_code = imx385_enum_mbus_code,
	.enum_frame_size = imx385_enum_frame_size,
	.enum_frame_interval = imx385_enum_frame_interval,
	.get_fmt = imx385_get_fmt,
	.set_fmt = imx385_set_fmt,
	.get_selection = imx385_get_selection,
};

static const struct v4l2_subdev_ops imx385_subdev_ops = {
	.video = &imx385_video_ops,
	.pad = &imx385_pad_ops,
};

static const struct media_entity_operations imx385_subdev_entity_ops = {
	.link_validate = v4l2_subdev_link_validate,
};

/*
 * Returns 0 if all link frequencies used by the driver for the given number
 * of MIPI data lanes are mentioned in the device tree, or the value of the
 * first missing frequency otherwise.
 */
static s64 imx385_check_link_freqs(const struct imx385 *imx385,
				   const struct v4l2_fwnode_endpoint *ep)
{
	int i, j;
	const s64 *freqs = imx385_link_freqs_ptr(imx385);
	int freqs_count = imx385_link_freqs_num(imx385);

	for (i = 0; i < freqs_count; i++) {
		for (j = 0; j < ep->nr_of_link_frequencies; j++)
			if (freqs[i] == ep->link_frequencies[j])
				break;
		if (j == ep->nr_of_link_frequencies)
			return freqs[i];
	}
	return 0;
}

static int imx385_probe(struct i2c_client *client)
{
	struct device *dev = &client->dev;
	struct fwnode_handle *endpoint;
	/* Only CSI2 is supported for now: */
	struct v4l2_fwnode_endpoint ep = {
		.bus_type = V4L2_MBUS_CSI2_DPHY
	};
	struct imx385 *imx385;
	const struct imx385_mode *mode;
	u32 xclk_freq;
	s64 fq;
	int ret;


	imx385 = devm_kzalloc(dev, sizeof(*imx385), GFP_KERNEL);

	imx385->sd.internal_ops = &imx385_internal_ops;
	v4l2_subdev_init(&imx385->sd, &imx385_subdev_ops);

	if (!imx385)
		return -ENOMEM;

	imx385->dev = dev;
	imx385->regmap = devm_regmap_init_i2c(client, &imx385_regmap_config);
	if (IS_ERR(imx385->regmap)) {
		dev_err(dev, "Unable to initialize I2C\n");
		return -ENODEV;
	}

	endpoint = fwnode_graph_get_next_endpoint(dev_fwnode(dev), NULL);
	if (!endpoint) {
		dev_err(dev, "Endpoint node not found\n");
		return -EINVAL;
	}

	ret = v4l2_fwnode_endpoint_alloc_parse(endpoint, &ep);
	fwnode_handle_put(endpoint);
	if (ret == -ENXIO) {
		dev_err(dev, "Unsupported bus type, should be CSI2\n");
		goto free_err;
	} else if (ret) {
		dev_err(dev, "Parsing endpoint node failed\n");
		goto free_err;
	}

	/* Get number of data lanes */
	imx385->nlanes = ep.bus.mipi_csi2.num_data_lanes;
	if (imx385->nlanes != 2 && imx385->nlanes != 4) {
		dev_err(dev, "Invalid data lanes: %d\n", imx385->nlanes);
		ret = -EINVAL;
		goto free_err;
	}

	dev_dbg(dev, "Using %u data lanes\n", imx385->nlanes);

	imx385->hmax_min = IMX385_HMAX_MIN;

	if (!ep.nr_of_link_frequencies) {
		dev_err(dev, "link-frequency property not found in DT\n");
		ret = -EINVAL;
		goto free_err;
	}

	/* Check that link frequences for all the modes are in device tree */
	fq = imx385_check_link_freqs(imx385, &ep);
	if (fq) {
		dev_err(dev, "Link frequency of %lld is not supported\n", fq);
		ret = -EINVAL;
		goto free_err;
	}

	/* get system clock (xclk) */
	imx385->xclk = devm_clk_get(dev, "xclk");
	if (IS_ERR(imx385->xclk)) {
		dev_err(dev, "Could not get xclk");
		ret = PTR_ERR(imx385->xclk);
		goto free_err;
	}

	ret = fwnode_property_read_u32(dev_fwnode(dev), "clock-frequency",
				       &xclk_freq);
	if (ret) {
		dev_err(dev, "Could not get xclk frequency\n");
		goto free_err;
	}

	/* external clock must be 37.125 MHz */
	if (xclk_freq != 37125000) {
		dev_err(dev, "External clock frequency %u is not supported\n",
			xclk_freq);
		ret = -EINVAL;
		goto free_err;
	}

	ret = clk_set_rate(imx385->xclk, xclk_freq);
	if (ret) {
		dev_err(dev, "Could not set xclk frequency\n");
		goto free_err;
	}

	ret = imx385_get_regulators(dev, imx385);
	if (ret < 0) {
		dev_err(dev, "Cannot get regulators\n");
		goto free_err;
	}

	mutex_init(&imx385->lock);

	/*
	 * Initialize the frame format. In particular, imx385->current_mode
	 * and imx385->bpp are set to defaults: imx385_calc_pixel_rate() call
	 * below relies on these fields.
	 */
	imx385_entity_init_state(&imx385->sd, NULL);

	v4l2_ctrl_handler_init(&imx385->ctrls, 32);

	imx385->analog_gain = v4l2_ctrl_new_std(&imx385->ctrls, &imx385_ctrl_ops,
			      V4L2_CID_ANALOGUE_GAIN, 0, 300, 1, 0);
	imx385->digital_gain = v4l2_ctrl_new_std(&imx385->ctrls, &imx385_ctrl_ops,
			       V4L2_CID_GAIN, 0, 420, 1, 0);
	mode = imx385->current_mode;
	imx385->hblank = v4l2_ctrl_new_std(&imx385->ctrls, &imx385_ctrl_ops,
					   V4L2_CID_HBLANK,
					   imx385->hmax_min - mode->width,
					   IMX385_HMAX_MAX - mode->width, 1,
					   mode->hmax);

	imx385->vblank = v4l2_ctrl_new_std(&imx385->ctrls, &imx385_ctrl_ops,
					   V4L2_CID_VBLANK,
					   mode->vmax - mode->height,
					   IMX385_VMAX_MAX - mode->height, 1,
					   mode->vmax - mode->height);

	imx385->exposure = v4l2_ctrl_new_std(&imx385->ctrls, &imx385_ctrl_ops,
					     V4L2_CID_EXPOSURE,
					     IMX385_EXPOSURE_MIN,
					     mode->vmax - 2,
					     IMX385_EXPOSURE_STEP,
					     mode->vmax - 2);
	imx385->link_freq =
		v4l2_ctrl_new_int_menu(&imx385->ctrls, &imx385_ctrl_ops,
				       V4L2_CID_LINK_FREQ,
				       imx385_link_freqs_num(imx385) - 1, 0,
				       imx385_link_freqs_ptr(imx385));
	if (imx385->link_freq)
		imx385->link_freq->flags |= V4L2_CTRL_FLAG_READ_ONLY;

	imx385->pixel_rate = v4l2_ctrl_new_std(&imx385->ctrls, &imx385_ctrl_ops,
					       V4L2_CID_PIXEL_RATE,
					       1, INT_MAX, 1,
					       imx385_calc_pixel_rate(imx385));

	v4l2_ctrl_new_std_menu_items(&imx385->ctrls, &imx385_ctrl_ops,
				     V4L2_CID_TEST_PATTERN,
				     ARRAY_SIZE(imx385_test_pattern_menu) - 1,
				     0, 0, imx385_test_pattern_menu);

	imx385->sd.ctrl_handler = &imx385->ctrls;

	if (imx385->ctrls.error) {
		dev_err(dev, "Control initialization error %d\n",
			imx385->ctrls.error);
		ret = imx385->ctrls.error;
		goto free_ctrl;
	}

	v4l2_i2c_subdev_init(&imx385->sd, client, &imx385_subdev_ops);
	imx385->sd.flags |= V4L2_SUBDEV_FL_HAS_DEVNODE;
	imx385->sd.dev = &client->dev;
	imx385->sd.entity.ops = &imx385_subdev_entity_ops;
	imx385->sd.entity.function = MEDIA_ENT_F_CAM_SENSOR;

	imx385->pad.flags = MEDIA_PAD_FL_SOURCE;
	ret = media_entity_pads_init(&imx385->sd.entity, 1, &imx385->pad);
	if (ret < 0) {
		dev_err(dev, "Could not register media entity\n");
		goto free_ctrl;
	}

	ret = v4l2_subdev_init_finalize(&imx385->sd);
	if (ret < 0) {
		dev_err(dev, "Subdev state finalize failed\n");
		media_entity_cleanup(&imx385->sd.entity);
		goto free_entity;

	}
	ret = v4l2_async_register_subdev(&imx385->sd);
	if (ret < 0) {
		dev_err(dev, "Could not register v4l2 device\n");
		goto free_entity;
	}

	/* Power on the device to match runtime PM state below */
	ret = imx385_power_on(dev);
	if (ret < 0) {
		dev_err(dev, "Could not power on the device\n");
		goto free_entity;
	}

	pm_runtime_set_active(dev);
	pm_runtime_enable(dev);
	pm_runtime_idle(dev);

	v4l2_fwnode_endpoint_free(&ep);

	return 0;

free_entity:
	media_entity_cleanup(&imx385->sd.entity);
free_ctrl:
	v4l2_ctrl_handler_free(&imx385->ctrls);
	mutex_destroy(&imx385->lock);
free_err:
	v4l2_fwnode_endpoint_free(&ep);

	return ret;
}

#if LINUX_VERSION_CODE <= KERNEL_VERSION(6,0,0)
static int imx385_remove(struct i2c_client *client)
#else
static void imx385_remove(struct i2c_client *client)
#endif
{
	struct v4l2_subdev *sd = i2c_get_clientdata(client);
	struct imx385 *imx385 = to_imx385(sd);

	v4l2_async_unregister_subdev(sd);
	media_entity_cleanup(&sd->entity);
	v4l2_ctrl_handler_free(sd->ctrl_handler);

	mutex_destroy(&imx385->lock);

	pm_runtime_disable(imx385->dev);
	if (!pm_runtime_status_suspended(imx385->dev))
		imx385_power_off(imx385->dev);
	pm_runtime_set_suspended(imx385->dev);

#if LINUX_VERSION_CODE <= KERNEL_VERSION(6,0,0)
	return 0;
#endif
}

static const struct of_device_id imx385_of_match[] = {
	{ .compatible = "sony,imx385" },
	{ /* sentinel */ }
};
MODULE_DEVICE_TABLE(of, imx385_of_match);

static struct i2c_driver imx385_i2c_driver = {
	.probe= imx385_probe,
	.remove = imx385_remove,
	.driver = {
		.name  = "imx385",
		.pm = &imx385_pm_ops,
		.of_match_table = of_match_ptr(imx385_of_match),
	},
};

module_i2c_driver(imx385_i2c_driver);

MODULE_DESCRIPTION("Sony IMX385 CMOS Image Sensor Driver");
MODULE_AUTHOR("FRAMOS GmbH");
MODULE_AUTHOR("Manivannan Sadhasivam <manivannan.sadhasivam@linaro.org>");
MODULE_LICENSE("GPL v2");
