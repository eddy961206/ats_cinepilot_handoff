from ats_cinepilot.ops.control_plugin_patch import patch_scs_sdk_controller_source


def test_patch_scs_sdk_controller_source_promotes_callback_context_to_static():
    source = """
struct input_context_t
{
    unsigned int input_idx = 0;
    unsigned int shm_offset = 0;
};

SCSAPI_RESULT scs_input_init(const scs_u32_t version, const scs_input_init_params_t *const params)
{
    input_context_t input_context;
    scs_input_device_t device_info;
    memset(&device_info, 0, sizeof(device_info));
    device_info.callback_context = &input_context;
    return SCS_RESULT_ok;
}
"""

    patched = patch_scs_sdk_controller_source(source)

    assert "static input_context_t g_input_context;" in patched
    assert "input_context_t input_context;" not in patched
    assert "device_info.callback_context = &g_input_context;" in patched


def test_patch_scs_sdk_controller_source_is_idempotent():
    source = """
struct input_context_t
{
    unsigned int input_idx = 0;
    unsigned int shm_offset = 0;
};
static input_context_t g_input_context;

SCSAPI_RESULT scs_input_init(const scs_u32_t version, const scs_input_init_params_t *const params)
{
    scs_input_device_t device_info;
    device_info.callback_context = &g_input_context;
    return SCS_RESULT_ok;
}
"""

    assert patch_scs_sdk_controller_source(source) == source
