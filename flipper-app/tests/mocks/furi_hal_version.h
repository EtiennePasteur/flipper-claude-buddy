#pragma once

/* Desktop test stub for furi_hal_version.h.
 *
 * Defines furi_mock_device_name as an extern so test_protocol.c can
 * set it per test case.  The inline function shadows the real Flipper
 * HAL call when compiled with -Imocks prepended to the include path.
 */
extern const char* furi_mock_device_name;

static inline const char* furi_hal_version_get_name_ptr(void) {
    return furi_mock_device_name;
}
