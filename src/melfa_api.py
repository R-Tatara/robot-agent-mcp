import ctypes
RcResult = int


# RcResult codes
class RcResultCode:
    #  @remark These constants represent the result codes returned by the API.
    #  @remark Do not modify these values. They are intended to be used as fixed constants (read-only).
    MR_OK: RcResult      = 0   # Request completed successfully
    MR_ER_SEND: RcResult = -1  # Failed to send data
    MR_ER_ARGS: RcResult = -2  # Invalid arguments provided
    MR_ER_RECV: RcResult = -3  # Failed to receive data
    MR_ER_DATA: RcResult = -4  # Invalid data received
    MR_ER_TOUT: RcResult = -5  # Operation timed out


# Slot status
class SlotState(ctypes.Structure):
    _fields_ = [("servo", ctypes.c_bool),
                ("err_no", ctypes.c_int),
                ("run_state", ctypes.c_bool),
                ("step_no", ctypes.c_int)]

    def __str__(self):
        return 'servo=%s, err_no=%d, run_state=%s, step_no=%d' % (
                self.servo, self.err_no, self.run_state, self.step_no)


# Joint
class Joint(ctypes.Structure):
    _fields_ = [("j1", ctypes.c_double),
                ("j2", ctypes.c_double),
                ("j3", ctypes.c_double),
                ("j4", ctypes.c_double),
                ("j5", ctypes.c_double),
                ("j6", ctypes.c_double),
                ("j7", ctypes.c_double),
                ("j8", ctypes.c_double)]

    def __str__(self):
        return 'j1=%.3lf, j2=%.3lf, j3=%.3lf, j4=%.3lf, j5=%.3lf, j6=%.3lf, j7=%.3lf, j8=%.3lf' % (
                self.j1, self.j2, self.j3, self.j4, self.j5, self.j6, self.j7, self.j8)


# Position
class Position(ctypes.Structure):
    _fields_ = [("x", ctypes.c_double),
                ("y", ctypes.c_double),
                ("z", ctypes.c_double),
                ("a", ctypes.c_double),
                ("b", ctypes.c_double),
                ("c", ctypes.c_double),
                ("fl1", ctypes.c_uint),
                ("fl2", ctypes.c_uint),
                ("l1", ctypes.c_double),
                ("l2", ctypes.c_double)]

    def __str__(self):
        return 'x=%.3lf, y=%.3lf, z=%.3lf, a=%.3lf, b=%.3lf, c=%.3lf, fl1=%.3lf, fl2=%.3lf, l1=%.3lf, l2=%.3lf' % (
                self.x, self.y, self.z, self.a, self.b, self.c, self.fl1, self.fl2, self.l1, self.l2)


# BasicInfo
class BasicInfo():
    rb_name:str = ""
    rc_name:str = ""
    fw_version:str = ""
    slot_max:int = 0

    def __str__(self):
        return 'rb_name=%s, rc_name=%s, fw_version=%s, slot_max=%d' % (
                self.rb_name, self.rc_name, self.fw_version, self.slot_max)


PATH_TO_LIB = "libmelfa_api.so"

client_lib = ctypes.cdll.LoadLibrary(PATH_TO_LIB)

class RobotController():
    ## @brief constructor
    #  @param ip_addr   [IN] IP address of the target controller
    #  @param port      [IN] Port number used for the connection
    #  @remark This constructor only specifies the target controller. It does not establish a connection at the tim
    #  @remark To establish a connection, please call the connect method separately.
    def __init__(self, ip_addr: str, port: int):
        ip_addr = ctypes.create_string_buffer(ip_addr.encode("UTF-8"))
        self.m_addr = ip_addr
        self.m_port = port
        client_lib.Create.restype = ctypes.c_void_p
        self.obj = client_lib.Create(self.m_addr, self.m_port)

    ## @brief destructor.
    def __del__(self):
        client_lib.Delete_obj.restype = ctypes.c_void_p
        client_lib.Delete_obj.argtypes = [ctypes.c_void_p]
        client_lib.Delete_obj(self.obj)

    ## @brief Establishes a connection
    #  @param ip_addr   [IN] IP address of the target controller
    #  @param port      [IN] Port number used for the connection
    #  @return 0:Success / Non-zero:Failure
    #  @remark If already connected, the current connection will be closed and reconnected
    def connect(self, ip_addr: str = "", port: int = 0) -> RcResult:
        ip_addr = ctypes.create_string_buffer(ip_addr.encode("UTF-8"))
        client_lib.Connect.restype = ctypes.c_int
        client_lib.Connect.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
        ret = client_lib.Connect(self.obj, ip_addr, port)
        return ret

    ## @brief Closes the connection
    #  @return 0:Success / Non-zero:Failure
    #  @remark This method returns successfully even if already disconnected
    def disconnect(self) -> RcResult:
        client_lib.Disconnect.restype = ctypes.c_int
        client_lib.Disconnect.argtypes = [ctypes.c_void_p]
        ret = client_lib.Disconnect(self.obj)
        return  ret

    ## @brief Sets the timeout duration
    #  @param msec [IN] Timeout value in milliseconds (must be 1 or greater)
    #  @remark The default value is 30000 ms (30 seconds)
    def set_timeout(self, msec:int) -> None:
        client_lib.Set_timeout.argtypes = [ctypes.c_void_p, ctypes.c_uint]
        client_lib.Set_timeout(self.obj, msec)
        return

    ## @brief Retrieves the timeout value
    #  @return Current timeout value in milliseconds
    def get_timeout(self) ->int:
        msec = 0
        client_lib.Get_timeout.restype = ctypes.c_int
        client_lib.Get_timeout.argtypes = [ctypes.c_void_p, ctypes.c_int]
        msec = client_lib.Get_timeout(self.obj, msec)
        return msec

    ## @brief Retrieves basic information
    #  @return 0:Success / Non-zero:Failure, BasicInfo(BasicInfo): BasicInfo Object
    def get_basic_info(self) -> tuple[RcResult, BasicInfo]:

        class BasicInfoCh(ctypes.Structure):
            _fields_ = [("ch_rb_name", ctypes.c_char * 30),
                        ("ch_rc_name", ctypes.c_char * 30),
                        ("ch_fw_version", ctypes.c_char * 30),
                        ("i_slot_max", ctypes.c_int)]

        # Initialize.
        basic_info_ch = BasicInfoCh()
        basic_info = BasicInfo()

        client_lib.Get_basic_info.restype = ctypes.c_int
        client_lib.Get_basic_info.argtypes = [ctypes.c_void_p, ctypes.POINTER(BasicInfoCh)]
        ret = client_lib.Get_basic_info(self.obj, basic_info_ch)

        # If there is a value, assign it to the BasicInfo member variable.
        if len(basic_info_ch.ch_rb_name) != 0:
            basic_info.rb_name =  basic_info_ch.ch_rb_name.decode()
        if len(basic_info_ch.ch_rc_name) != 0:
            basic_info.rc_name = basic_info_ch.ch_rc_name.decode()
        if len(basic_info_ch.ch_fw_version) != 0:
            basic_info.fw_version =  basic_info_ch.ch_fw_version.decode()
        if (basic_info_ch.i_slot_max != 0):
            basic_info.slot_max = basic_info_ch.i_slot_max

        return (ret, basic_info)

    ## @brief Turns the servo ON or OFF
    #  @param onoff [IN] true to turn ON, false to turn OFF
    #  @return 0:Success / Non-zero:Failure
    def turn_servo(self, onoff:bool) -> RcResult:
        client_lib.Turn_servo.restype = ctypes.c_int
        client_lib.Turn_servo.argtypes = [ctypes.c_void_p, ctypes.c_bool]
        ret = client_lib.Turn_servo(self.obj, onoff)
        return  ret

    ## @brief Sets the override value
    #  @param ovrd [IN] Override value (Unit: %, Range : 1-100)
    #  @return 0:Success / Non-zero:Failure
    def set_override(self, ovrd:int) -> RcResult:
        client_lib.Set_override.restype = ctypes.c_int
        client_lib.Set_override.argtypes = [ctypes.c_void_p, ctypes.c_int]
        ret = client_lib.Set_override(self.obj, ovrd)
        return ret

    ## @brief Retrieves the current override value
    #  @return 0:Success / Non-zero:Failure , ovrd(int):Override Value
    def get_override(self) -> tuple[RcResult, int]:
        ovrd = ctypes.c_uint()
        client_lib.Get_override.restype = ctypes.c_int
        client_lib.Get_override.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint)]
        ret = client_lib.Get_override(self.obj, ovrd)
        return (ret, ovrd.value)

    ## @brief  Retrieves the status of the specified slot
    #  @param slot_no(int) [IN] SlotState Object to store the result
    #  @return 0:Success / Non-zero:Failure , SlotState(SlotState):SlotState Object
    def get_slot_state(self, slot_no: int = 1) -> tuple[RcResult, SlotState]:
        state = SlotState()
        client_lib.Get_slot_state.restype = ctypes.c_int
        client_lib.Get_slot_state.argtypes = [ctypes.c_void_p, ctypes.POINTER(SlotState), ctypes.c_int]
        ret = client_lib.Get_slot_state(self.obj, state, slot_no)
        return (ret, state)

    ## @brief Starts the program
    #  @param slot_no [IN] Slot number (0: All slots / 1 or higher: Specific slot) (Range: 0–Max slot)
    #  @param prg_name(str) [IN] Program name (Empty: Select program / Non-empty: Run specified program)
    #  @param mode(int) [IN] 0:Continuous/ 1:Cyclic
    #  @return 0:Success / Non-zero:Failure
    def start(self, slot_no: int = 0, prg_name: str = "", mode: int = 0) -> RcResult:
        prg_name = ctypes.create_string_buffer(prg_name.encode("UTF-8"))
        client_lib.Start.restype = ctypes.c_int
        client_lib.Start.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
        ret = client_lib.Start(self.obj, slot_no, prg_name, mode)
        return ret

    ## @brief Stops the program
    #  @param slot_no [IN] Slot number (0: All slots / 1 or higher: Specific slot) (Range: 0–Max slot)
    #  @return 0:Success / Non-zero:Failure
    def stop(self, slot_no: int = 0) -> RcResult:
        client_lib.Stop.restype = ctypes.c_int
        client_lib.Stop.argtypes = [ctypes.c_void_p, ctypes.c_int]
        ret = client_lib.Stop(self.obj, slot_no)
        return ret

    ## @brief Resets the program
    #  @param slot_no [IN] Slot number (0: All slots / 1 or higher: Specific slot) (Range: 0–Max slot)
    #  @return 0:Success / Non-zero:Failure
    def reset(self, slot_no: int = 0) -> RcResult:
        client_lib.Reset.restype = ctypes.c_int
        client_lib.Reset.argtypes = [ctypes.c_void_p, ctypes.c_int]
        ret = client_lib.Reset(self.obj, slot_no)
        return ret

    ## @brief Initializes the program slot
    #  @return 0:Success / Non-zero:Failure
    def init_slot(self) -> RcResult:
        client_lib.Init_slot.restype = ctypes.c_int
        client_lib.Init_slot.argtypes = [ctypes.c_void_p]
        ret = client_lib.Init_slot(self.obj)
        return ret

    ## @brief Executes a command directly
    #  @param code(str) [IN] Command string
    #  @param timeout(int) [IN] Timeout value (Unit: ms). See remarks for details
    #  @param slot_no(int) [IN] Slot number (Range: 1–Max slot)
    #  @return 0:Success / Non-zero:Failure
    #  @remark timeout is 1 or less: Do not wait for execution to complete
    #  @remark timeout is 0: Wait until execution completes (ignores value set by set_timeout)
    #  @remark timeout is 1 or more: Wait for the specified time (ignores value set by set_timeout)
    #  @remark If execution does not complete within the specified time, a timeout error occurs
    def direct(self, code: str, timeout: int = 0, slot_no: int = 1) -> RcResult:
        code = ctypes.create_string_buffer(code.encode("UTF-8"))
        client_lib.Direct.restype = ctypes.c_int
        client_lib.Direct.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_int]
        ret = client_lib.Direct(self.obj, code, timeout, slot_no)
        return ret

    ## @brief Reads the value of an integer-type variable
    #  @param val_name [IN] Variable name
    #  @param slot_no [IN] Slot number (Range: 1–Max slot)
    #  @return 0:Success / Non-zero:Failure, val(int)
    def get_val_integer(self, val_name: str, slot_no: int = 1) -> tuple[RcResult, ctypes.c_int]:
        val = ctypes.c_int()
        val_name = ctypes.create_string_buffer(val_name.encode("UTF-8"))
        client_lib.Get_val_integer.restype = ctypes.c_int
        client_lib.Get_val_integer.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int), ctypes.c_char_p, ctypes.c_int]
        ret = client_lib.Get_val_integer(self.obj, val, val_name, slot_no)
        return (ret, val.value)

    ## @brief Reads the value of a float-type variable
    #  @param val_name [IN] Variable name
    #  @param slot_no [IN] Slot number (Range: 1–Max slot)
    #  @return 0:Success / Non-zero:Failure, val(double)
    def get_val_float(self, val_name: str, slot_no: int = 1) -> tuple[RcResult, ctypes.c_double]:
        val = ctypes.c_double()
        val_name = ctypes.create_string_buffer(val_name.encode("UTF-8"))
        client_lib.Get_val_float.restype = ctypes.c_int
        client_lib.Get_val_float.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_double), ctypes.c_char_p, ctypes.c_int]
        ret = client_lib.Get_val_float(self.obj, val, val_name, slot_no)
        return (ret, val.value)

    ## @brief Reads the value of a string-type variable
    #  @param val_name [IN] Variable name
    #  @param slot_no [IN] Slot number (Range: 1–Max slot)
    #  @return 0:Success / Non-zero:Failure, val(Str)
    def get_val_chars(self, val_name: str, slot_no: int = 1) -> tuple[RcResult, str]:
        # Max number of characters in buffer
        buflen = 127
        byte_val = ctypes.create_string_buffer(buflen)
        val_name = ctypes.create_string_buffer(val_name.encode("UTF-8"))
        client_lib.Get_val_chars.restype = ctypes.c_int
        client_lib.Get_val_chars.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
        ret = client_lib.Get_val_chars(self.obj, byte_val, val_name, slot_no)

        # If there is a value, assign it to the val variable.
        val = ""
        if len(byte_val.value) != 0:
            val = byte_val.value.decode()

        return (ret, val)

    ## @brief Reads the value of a position-type variable
    #  @param val_name [IN] Variable name
    #  @param slot_no [IN] Slot number (Range: 1–Max slot)
    #  @return 0:Success / Non-zero:Failure, val(Position)
    def get_val_pos(self, val_name: str, slot_no: int = 1) -> tuple[RcResult, Position]:
        position = Position()
        val_name = ctypes.create_string_buffer(val_name.encode("UTF-8"))
        client_lib.Get_val_pos.restype = ctypes.c_int
        client_lib.Get_val_pos.argtypes = [ctypes.c_void_p, ctypes.POINTER(Position), ctypes.c_char_p, ctypes.c_int]
        ret = client_lib.Get_val_pos(self.obj, position, val_name, slot_no)
        return (ret, position)

    ## @brief Reads the value of a joint-type variable
    #  @param val_name [IN] Variable name
    #  @param slot_no [IN] Slot number (Range: 1–Max slot)
    #  @return 0:Success / Non-zero:Failure, val(Joint)
    def get_val_joint(self, val_name: str, slot_no: int = 1) -> tuple[RcResult, Joint]:
        joint = Joint()
        val_name = ctypes.create_string_buffer(val_name.encode("UTF-8"))
        client_lib.Get_val_joint.restype = ctypes.c_int
        client_lib.Get_val_joint.argtypes = [ctypes.c_void_p, ctypes.POINTER(Joint), ctypes.c_char_p, ctypes.c_int]
        ret = client_lib.Get_val_joint(self.obj, joint, val_name, slot_no)
        return (ret, joint)

    ## @brief Resets the error
    # @return 0:Success / Non-zero:Failure
    def reset_error(self) -> RcResult:
        client_lib.Reset_error.restype = ctypes.c_int
        client_lib.Reset_error.argtypes = [ctypes.c_void_p]
        ret = client_lib.Reset_error(self.obj)
        return ret

    ## @brief Get the current joint positions
    #  @return 0:Success / Non-zero:Failure, joint(Joint)
    def get_curpos_joint(self) -> tuple[RcResult, Joint]:
        joint = Joint()
        client_lib.Get_curpos_joint.restype = ctypes.c_int
        client_lib.Get_curpos_joint.argtypes = [ctypes.c_void_p, ctypes.POINTER(Joint)]
        ret = client_lib.Get_curpos_joint(self.obj, joint)
        return (ret, joint)

    ## @brief Get the current position in XYZ coordinates
    #  @return 0:Success / Non-zero:Failure, position(Position)
    def get_curpos_xyz(self) -> tuple[RcResult, Position]:
        position = Position()
        client_lib.Get_curpos_xyz.restype = ctypes.c_int
        client_lib.Get_curpos_xyz.argtypes = [ctypes.c_void_p, ctypes.POINTER(Position)]
        ret = client_lib.Get_curpos_xyz(self.obj, position)
        return (ret, position)
