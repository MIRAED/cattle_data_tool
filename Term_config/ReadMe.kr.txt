1. 매크로 테스트 방법.
미리 정의된 파일을 Default_command.xlsx 로 복사한 후 툴 실행.

* 에이징 테스트용 매크로 파일
1. CDC : macro_MPW2_SJIT_fp_5g_temperature_CDC_Test_continue.xlsx
2. TDC : macro_MPW2_SJIT_TDC_Scan_fp_5g_3byte_apply_TDC_Test_internal_clk_continue.xlsx

* 미리 정의된 매크로파일 
1. macro_MPW2_SJIT_fp_5g_temperature_10times_CDC_Test.xlsx
  -> CDC테스트 10회 진행
2. macro_MPW2_SJIT_fp_5g_temperature_CDC_Test_continue.xlsx
  -> CDC테스트 에이징
3. macro_MPW2_SJIT_TDC_Scan_fp_5g_3byte_apply_TDC_Test.xlsx
  -> TDC테스트를 진행
4. macro_MPW2_SJIT_TDC_Scan_fp_5g_3byte_apply_TDC_Test_fast.xlsx
  -> TDC테스트를 빠르게 진행
5. macro_MPW2_SJIT_TDC_Scan_fp_5g_3byte_apply_TDC_Test_internal_clk.xlsx
  -> TDC테스트를 인터널 클럭으로 진행
6. macro_MPW2_SJIT_TDC_Scan_fp_5g_3byte_apply_TDC_Test_internal_clk_continue.xlsx
  -> TDC테스트를 연속해서 인터널 클럭으로 진행

* CDC 테스트 커맨드
- 장치하나 빠르게 테스트
MPW_I2C_ADDR_CHANGE 0xA0;;;MPW_OSC_MODE 1 0;;;MPW_CDC_TEST  6 0 20 10
- 장치를 순차적으로 변경해가면서 빠르게 테스트
MPW_I2C_ADDR_CHANGE;;;MPW_OSC_MODE 1 0;;;MPW_CDC_TEST  6 0 20 10

* TDC테스트 커맨드
- 장치하나 빠르게 테스트 (외부클럭사용)
MPW_I2C_ADDR_CHANGE 0xA0;;;MPW_SET_INT_CLK 0;;;MPW_OSC_MODE 1 0;;;MPW_TDC_SCAN 6 1 8;;;;;;;;;;;;;;;;;;;;MPW_TDC_TEST  FFFFFF 6 10 10
- 장치하나 빠르게 테스트 (내부클럭사용)
MPW_I2C_ADDR_CHANGE 0xA0;;;MPW_SET_INT_CLK 1;;;MPW_OSC_MODE 1 0;;;MPW_TDC_SCAN 6 1 8;;;;;;;;;;;;;;;;;;;;MPW_TDC_TEST  FFFFFF 6 10 10
- 장치를 순차적으로 변경해가면서 빠르게 테스트 (외부클럭사용)
MPW_I2C_ADDR_CHANGE 0xA0;;;MPW_SET_INT_CLK 0;;;MPW_OSC_MODE 1 0;;;MPW_TDC_SCAN 6 1 8;;;;;;;;;;;;;;;;;;;;MPW_TDC_TEST  FFFFFF 6 10 10
