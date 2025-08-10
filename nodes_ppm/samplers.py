from comfy.comfy_types.node_typing import IO, ComfyNodeABC, InputTypeDict
from comfy.k_diffusion import sampling as k_diffusion_sampling
from comfy.model_patcher import ModelPatcher
from comfy.samplers import KSAMPLER

from ..sampling import ppm_cfgpp_dyn_sampling, ppm_cfgpp_sampling, ppm_dyn_sampling, ppm_sampling

CFGPP_SAMPLER_NAMES_COMFY_ETA: list = [
    "euler_ancestral_cfg_pp",
]
CFGPP_SAMPLER_NAMES_COMFY: list = [
    "euler_cfg_pp",
    "dpmpp_2m_cfg_pp",
    "gradient_estimation_cfg_pp",
    *CFGPP_SAMPLER_NAMES_COMFY_ETA,
]


CFGPP_SAMPLER_NAMES: list = [
    *CFGPP_SAMPLER_NAMES_COMFY,
    *ppm_cfgpp_sampling.CFGPP_SAMPLER_NAMES_KD,
    *ppm_cfgpp_dyn_sampling.CFGPP_SAMPLER_NAMES_DYN,
]
SAMPLER_NAMES_ETA: list = [
    *CFGPP_SAMPLER_NAMES_COMFY_ETA,
    *ppm_cfgpp_sampling.CFGPP_SAMPLER_NAMES_KD_ETA,
    *ppm_cfgpp_dyn_sampling.CFGPP_SAMPLER_NAMES_DYN_ETA,
    *ppm_dyn_sampling.SAMPLER_NAMES_DYN_ETA,
]


class DynSamplerSelect(ComfyNodeABC):
    @classmethod
    def INPUT_TYPES(cls) -> InputTypeDict:
        return {
            "required": {
                "sampler_name": (IO.COMBO, {"options": ppm_dyn_sampling.SAMPLER_NAMES_DYN}),
                "eta": (IO.FLOAT, {"default": 1.0, "min": 0.0, "max": 100.0, "step": 0.01, "round": False}),
                "s_dy_pow": (IO.INT, {"default": 2, "min": -1, "max": 100}),
                "s_extra_steps": (IO.BOOLEAN, {"default": False}),
            }
        }

    RETURN_TYPES = (IO.SAMPLER,)
    CATEGORY = "sampling/custom_sampling/samplers"

    FUNCTION = "get_sampler"

    def get_sampler(self, sampler_name: str, eta=1.0, s_dy_pow=-1, s_extra_steps=False):
        sampler_func = getattr(ppm_dyn_sampling, "sample_{}".format(sampler_name))
        extra_options = {}
        if sampler_name in SAMPLER_NAMES_ETA:
            extra_options["eta"] = eta
        extra_options["s_dy_pow"] = s_dy_pow
        extra_options["s_extra_steps"] = s_extra_steps
        sampler = KSAMPLER(sampler_func, extra_options=extra_options)
        return (sampler,)


# More CFG++ samplers based on https://github.com/comfyanonymous/ComfyUI/pull/3871 by yoinked-h
class CFGPPSamplerSelect(ComfyNodeABC):
    @classmethod
    def INPUT_TYPES(cls) -> InputTypeDict:
        return {
            "required": {
                "sampler_name": (IO.COMBO, {"options": CFGPP_SAMPLER_NAMES}),
                "eta": (IO.FLOAT, {"default": 1.0, "min": 0.0, "max": 100.0, "step": 0.01, "round": False}),
                "s_gamma_start": (IO.FLOAT, {"default": 0.0, "min": 0.0, "max": 10000.0, "step": 0.01, "round": False}),
                "s_gamma_end": (IO.FLOAT, {"default": 1.0, "min": 0.0, "max": 10000.0, "step": 0.01, "round": False}),
                "s_extra_steps": (IO.BOOLEAN, {"default": False}),
            }
        }

    RETURN_TYPES = (IO.SAMPLER,)
    CATEGORY = "sampling/custom_sampling/samplers"

    FUNCTION = "get_sampler"

    def get_sampler(self, sampler_name: str, eta=1.0, s_gamma_start=0.0, s_gamma_end=1.0, s_extra_steps=False):
        sampler_func = self._get_sampler_func(sampler_name)
        extra_options = {}
        if sampler_name in SAMPLER_NAMES_ETA:
            extra_options["eta"] = eta
        if sampler_name in ppm_cfgpp_dyn_sampling.CFGPP_SAMPLER_NAMES_DYN:
            extra_options["s_gamma_start"] = s_gamma_start
            extra_options["s_gamma_end"] = s_gamma_end
            extra_options["s_extra_steps"] = s_extra_steps
        sampler = KSAMPLER(sampler_func, extra_options=extra_options)
        return (sampler,)

    def _get_sampler_func(self, sampler_name: str):
        if sampler_name in CFGPP_SAMPLER_NAMES_COMFY:
            return getattr(k_diffusion_sampling, "sample_{}".format(sampler_name))
        if sampler_name in ppm_cfgpp_sampling.CFGPP_SAMPLER_NAMES_KD:
            return getattr(ppm_cfgpp_sampling, "sample_{}".format(sampler_name))
        if sampler_name in ppm_cfgpp_dyn_sampling.CFGPP_SAMPLER_NAMES_DYN:
            return getattr(ppm_cfgpp_dyn_sampling, "sample_{}".format(sampler_name))

        raise ValueError(f"Unknown sampler_name {sampler_name}")


class PPMSamplerSelect(ComfyNodeABC):
    @classmethod
    def INPUT_TYPES(cls) -> InputTypeDict:
        return {
            "required": {
                "sampler_name": (IO.COMBO, {"options": ppm_sampling.SAMPLER_NAMES}),
                "model": (IO.MODEL, {}),
                "cfg_pp": (IO.BOOLEAN, {"default": False}),
                "s_sigma_diff": (IO.FLOAT, {"default": 2.0, "min": 0.0, "max": 10000.0, "step": 0.01, "round": False}),
            }
        }

    RETURN_TYPES = (IO.SAMPLER,)
    CATEGORY = "sampling/custom_sampling/samplers"

    FUNCTION = "get_sampler"

    def get_sampler(self, sampler_name: str, model: ModelPatcher, cfg_pp=False, s_sigma_diff=2.0):
        sampler_func = getattr(ppm_sampling, "sample_{}".format(sampler_name))
        ms = model.get_model_object("model_sampling")
        extra_options = {}
        extra_options["cfg_pp"] = cfg_pp
        extra_options["s_sigma_diff"] = s_sigma_diff
        extra_options["s_sigma_max"] = ms.sigma_max
        sampler = KSAMPLER(sampler_func, extra_options=extra_options)
        return (sampler,)


class SamplerGradientEstimation(ComfyNodeABC):
    @classmethod
    def INPUT_TYPES(cls) -> InputTypeDict:
        return {
            "required": {
                "sampler_name": (IO.COMBO, {"options": ["gradient_estimation", "gradient_estimation_cfg_pp"]}),
                "gamma": (IO.FLOAT, {"default": 2.0, "min": 2.0, "max": 5.0, "step": 0.01, "round": 0.001}),
            }
        }

    RETURN_TYPES = (IO.SAMPLER,)
    CATEGORY = "sampling/custom_sampling/samplers"

    FUNCTION = "get_sampler"

    def get_sampler(self, sampler_name: str, gamma=2.0):
        sampler_func = getattr(k_diffusion_sampling, "sample_{}".format(sampler_name))
        extra_options = {}
        extra_options["ge_gamma"] = gamma
        sampler = KSAMPLER(sampler_func, extra_options=extra_options)
        return (sampler,)


NODE_CLASS_MAPPINGS = {
    "CFGPPSamplerSelect": CFGPPSamplerSelect,
    "DynSamplerSelect": DynSamplerSelect,
    "PPMSamplerSelect": PPMSamplerSelect,
    "SamplerGradientEstimation": SamplerGradientEstimation,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CFGPPSamplerSelect": "CFG++SamplerSelect",
    "DynSamplerSelect": "DynSamplerSelect",
    "PPMSamplerSelect": "PPMSamplerSelect",
    "SamplerGradientEstimation": "SamplerGradientEstimation",
}
