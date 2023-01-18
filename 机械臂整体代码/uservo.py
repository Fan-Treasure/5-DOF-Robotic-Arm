
import time
import logging
import serial
import struct


class Packet:


	PKT_TYPE_REQUEST = 0
	PKT_TYPE_RESPONSE = 1
	HEADER_LEN = 2
	HEADERS = [b'\x12\x4c', b'\x05\x1c']
	CODE_LEN = 1
	SIZE_LEN = 1
	CHECKSUM_LEN = 1

	@classmethod
	def calc_checksum(cls, code, param_bytes=b'', pkt_type=1):

		header = cls.HEADERS[pkt_type]
		return sum(header + struct.pack('<BB', code, len(param_bytes)) + param_bytes) %256

	@classmethod
	def verify(cls, packet_bytes, pkt_type=1):

		header = cls.HEADERS[pkt_type]

		if packet_bytes[:cls.HEADER_LEN] != cls.HEADERS[pkt_type]:
			return False
		code, size = struct.unpack('<BB', packet_bytes[cls.HEADER_LEN : cls.HEADER_LEN + cls.CODE_LEN + cls.SIZE_LEN])

		param_bytes = packet_bytes[cls.HEADER_LEN + cls.CODE_LEN + cls.SIZE_LEN : -cls.CHECKSUM_LEN]
		if len(param_bytes) != size:
			return False

		checksum = packet_bytes[-cls.CHECKSUM_LEN]

		if checksum != cls.calc_checksum(code , param_bytes, pkt_type=pkt_type):
			return False

		return True

	@classmethod
	def pack(cls, code, param_bytes=b''):
		size = len(param_bytes)
		checksum = cls.calc_checksum(code, param_bytes, pkt_type=cls.PKT_TYPE_REQUEST)
		frame_bytes = cls.HEADERS[cls.PKT_TYPE_REQUEST] + struct.pack('<BB', code, size) + param_bytes + struct.pack('<B', checksum)
		return frame_bytes
	
	@classmethod
	def unpack(cls, packet_bytes):
		if not cls.verify(packet_bytes, pkt_type=cls.PKT_TYPE_RESPONSE):
			return None
		code = struct.unpack('<B', packet_bytes[cls.HEADER_LEN:cls.HEADER_LEN+cls.CODE_LEN])[0]
		param_bytes = packet_bytes[cls.HEADER_LEN + cls.CODE_LEN + cls.SIZE_LEN : -cls.CHECKSUM_LEN]
		return code, param_bytes

class PacketBuffer:
	def __init__(self, is_debug=False):
		self.is_debug = is_debug
		self.packet_bytes_list = []
		self.empty_buffer()
	
	def update(self, next_byte):
		if not self.header_flag:
			if len(self.header) < Packet.HEADER_LEN:
				self.header += next_byte
				if len(self.header) == Packet.HEADER_LEN and self.header == Packet.HEADERS[Packet.PKT_TYPE_RESPONSE]:
					self.header_flag = True
			elif len(self.header) == Packet.HEADER_LEN:
				self.header = self.header[1:] + next_byte
				if self.header == Packet.HEADERS[Packet.PKT_TYPE_RESPONSE]:
					self.header_flag = True
		elif not self.code_flag:
			if len(self.code) < Packet.CODE_LEN:
				self.code += next_byte
				if len(self.code) == Packet.CODE_LEN:
					# print('code: {}'.format(self.code))
					self.code_flag = True
		elif not self.size_flag:
			if len(self.size) < Packet.SIZE_LEN:
				self.size += next_byte
				if len(self.size) == Packet.SIZE_LEN:
					self.size_flag = True
					self.param_len = struct.unpack('<B', self.size)[0]
		elif not self.param_bytes_flag:
			if len(self.param_bytes) < self.param_len:
				self.param_bytes += next_byte
				if len(self.param_bytes) == self.param_len:
					self.param_bytes_flag = True
		else:
			tmp_packet_bytes = self.header + self.code + self.size + self.param_bytes + next_byte
			
			ret = Packet.verify(tmp_packet_bytes, pkt_type=Packet.PKT_TYPE_RESPONSE)
			
			if ret:
				self.checksum_flag = True
				self.packet_bytes_list.append(tmp_packet_bytes)

			self.empty_buffer()
		
	def empty_buffer(self):
		self.param_len = None
		self.header = b''
		self.header_flag = False
		self.code = b''
		self.code_flag = False
		self.size = b''
		self.size_flag = False
		self.param_bytes = b''
		self.param_bytes_flag = False
	
	def has_valid_packet(self):
		return len(self.packet_bytes_list) > 0
	
	def get_packet(self):
		return self.packet_bytes_list.pop(0)


class UartServoInfo:
	SERVO_DEADBLOCK = 1.0
	SERVO_ANGLE_LOWERB = -135
	SERVO_ANGLE_UPPERB = 135
	
	def __init__(self, id, lowerb=None, upperb=None):
		self.id = id
		self.cur_angle = None
		self.target_angle = None
		self.is_online = False
		self.lowerb = lowerb if lowerb is not None else None
		self.upperb = upperb if upperb is not None else None
		
		self.last_angle_error = None
		self.last_sample_time = None
		self.data_table_raw_dict = {}
		self.data_write_success = False
		self.is_mturn = False
	
	def is_stop(self):
		if self.target_angle is None:
			self.target_angle = self.cur_angle
		angle_error = self.target_angle - self.cur_angle
		if abs(angle_error) <= self.SERVO_DEADBLOCK:
			return True
		
		if self.last_angle_error is None:
			self.last_angle_error = angle_error
			self.last_sample_time = time.time()

		if abs(self.last_angle_error - angle_error) > 0.2:
			self.last_angle_error = angle_error
			self.last_sample_time = time.time()

		if (time.time() - self.last_sample_time) > 1:
			# 
			self.last_angle_error = None
			self.last_sample_time = None
			return True
		
		return False
	
	@property
	def angle(self):
		return self.cur_angle
	
	def move(self, angle):
		if self.lowerb is not None:
			angle = self.lowerb if angle < self.lowerb else angle
		if self.upperb is not None:
  			angle = self.upperb if angle > self.upperb else angle
		self.target_angle = angle

	def update(self, angle):
		self.cur_angle = angle
	
	def __str__(self):
		return "目标角度:{:.1f} 实际角度:{:.1f} 角度误差:{:.2f}".format(self.target_angle, self.angle, self.target_angle-self.angle)

class UartServoManager:
	UPDATE_INTERVAL_MS = 10 # ms
	CODE_PING = 1
	CODE_QUERY_SERVO_ANGLE = 10
	CODE_QUERY_SERVO_ANGLE_MTURN = 16
	CODE_QUERY_SERVO_INFO = 5
	CODE_SET_SERVO_ANGLE = 8
	CODE_SET_SPIN = 7
	CODE_SET_DAMPING = 9
	CODE_SET_SERVO_ANGLE_BY_INTERVAL = 11
	CODE_SET_SERVO_ANGLE_BY_VELOCITY = 12
	CODE_SET_SERVO_ANGLE_MTURN = 13
	CODE_SET_SERVO_ANGLE_MTURN_BY_INTERVAL = 14
	CODE_SET_SERVO_ANGLE_MTURN_BY_VELOCITY = 15
	CODE_RESET_USER_DATA = 2
	CODE_READ_DATA = 3
	CODE_WRITE_DATA = 4

	RESPONSE_CODE_NEGLECT = []
	WHEEL_MODE_STOP = 0x00
	WHEEL_MODE_NORMAL = 0x01
	WHEEL_MODE_TURN = 0x02
	WHEEL_MODE_TIME = 0x03
	ADDRESS_VOLTAGE = 1
	ADDRESS_CURRENT = 2
	ADDRESS_POWER = 3
	ADDRESS_TEMPERATURE = 4
	def __init__(self, uart, is_scan_servo=True, srv_num=254, mean_dps=100, is_debug=False):
		self.is_debug = is_debug
		self.uart = uart
		self.pkt_buffer = PacketBuffer()
		self.mean_dps = mean_dps
		self.servos = {}
		

		self.response_handle_funcs = {
			self.CODE_QUERY_SERVO_ANGLE: self.response_query_servo_angle,
			self.CODE_QUERY_SERVO_ANGLE_MTURN: self.response_query_servo_angle_mturn,
			self.CODE_PING: self.response_ping,
			self.CODE_RESET_USER_DATA: self.response_reset_user_data,
			self.CODE_READ_DATA: self.response_read_data,
			self.CODE_WRITE_DATA: self.response_write_data,
		}

		if is_scan_servo:
			self.scan_servo(srv_num=srv_num)

	def send_request(self, code, param_bytes):
		packet_bytes = Packet.pack(code, param_bytes)
		try:
			self.uart.write(packet_bytes)
		except serial.SerialException as e:
			logging.error('串口数据发送异常, 请检查是否是USB口松动或设备号变更, 需重新初始化舵机')
			# 

	def ping(self, servo_id:int):
		# self.cur_ping_servo_id = servo_id #　为了可视化显示
		self.send_request(self.CODE_PING, struct.pack('<B', servo_id))
		if self.is_debug:
			logging.info('PING 舵机 id={}'.format(servo_id))
		self.update(wait_response=True)
		ret = servo_id in self.servos
		if self.is_debug and ret:
			logging.info('[fs_uservo]舵机ID={} 响应ping'.format(servo_id))
		if ret:
			self.query_servo_angle(servo_id)
		return ret

	def scan_servo(self, srv_num=254):
		for servo_id in range(srv_num):
			self.ping(servo_id)
		if self.is_debug:
			logging.info("有效的舵机ID列表: {}".format(list(self.servos.keys())))
	
	def response_ping(self, param_bytes):
		servo_id, = struct.unpack('<B', param_bytes)
		if servo_id not in self.servos:
			self.servos[servo_id] = UartServoInfo(servo_id)
			self.servos[servo_id].is_online = True # 设置舵机在线的标志位
			if self.is_debug:
				logging.info('[fs_uservo]ECHO 添加一个新的舵机 id={}'.format(servo_id))
		else:
			self.servos[servo_id].is_online = True # 设置舵机在线的标志位
			if self.is_debug:
				logging.info('[fs_uservo]ECHO 已知舵机 id={}'.format(servo_id))
		

	def query_servo_angle(self, servo_id):
		if self.is_debug:
			logging.info('查询单个舵机的角度 id={}'.format(servo_id))
		if self.servos[servo_id].is_mturn:
			self.send_request(self.CODE_QUERY_SERVO_ANGLE_MTURN, struct.pack('<B', servo_id))
		else:
			self.send_request(self.CODE_QUERY_SERVO_ANGLE, struct.pack('<B', servo_id))
		self.update(wait_response=True) # 等待数据回传
		return self.servos[servo_id].angle

	def query_all_srv_angle(self):
		for servo_id in self.servos:
			self.query_servo_angle(servo_id)

	def response_query_servo_angle(self, param_bytes):
		servo_id, angle = struct.unpack('<Bh', param_bytes)
		angle /= 10
		if servo_id not in self.servos:
			pass
		else:
			self.servos[servo_id].update(angle)
			if self.is_debug:
				logging.info('[INFO] 更新舵机角度 id={}  角度: {:.2f} deg'.format(servo_id, angle))
	def response_query_servo_angle_mturn(self, param_bytes):
		servo_id, angle, mturn = struct.unpack('<Bih', param_bytes)
		angle /= 10.0
		
		if servo_id not in self.servos:
			pass
		else:
			self.servos[servo_id].update(angle)
			if self.is_debug:
				logging.info('[INFO] 更新舵机角度 id={}  角度: {:.2f} deg'.format(servo_id, angle))
	
	def refresh_srv_list(self, max_servo_id=254):
		self.servos = {}
		for servo_idx in range(max_servo_id):
			self.ping(servo_idx)
			for ti in range(20):
				self.update()
				if servo_idx in self.servos:
					break
				
				time.sleep(0.05)

	def query_srv_info(self, servo_id):
		self.send_request(self.CODE_QUERY_SERVO_INFO, struct.pack('<B', servo_id))
		# logging.info('查询单个舵机的所有配置 id={}'.format(servo_id))
		self.update(wait_response=True)

	def set_servo_angle(self, servo_id:int, angle:float, is_mturn:bool=False, interval:float=None, velocity:float=None, t_acc:int=20, t_dec:int=20,  power:int=0, mean_dps:float=100.0):
		'''发送舵机角度控制请求
		@param servo_id 
			舵机的ID号
		@param angle 
			舵机的目标角度
		@param is_mturn
			是否开启多圈模式
		@param interval 
			中间间隔 单位ms
		@param velocity 
			目标转速，单位dps
		@param t_acc
			加速时间，在指定目标转速时有效. 单位ms
		@param t_dec
			减速时间, 在指定减速时间时有效. 单位ms
		@param power
			功率限制, 单位mW
		@param mean_dps
			平均转速, 单位dps
		'''
		if servo_id not in self.servos:
			logging.warn('未知舵机序号: {}'.format(servo_id))
			return False

		self.servos[servo_id].move(angle)

		angle = int(angle * 10)

		if is_mturn:
			if angle < -3686400:
				angle = -3686400
			elif angle > 3686400:
				angle = 3686400
		else:
			if angle < -1800:
				angle = -1800
			elif angle > 1800:
				angle = 1800

		if t_acc < 20:
			t_acc = 20
		if t_dec < 20:
			t_dec = 20

		srv_info = self.servos[servo_id]
		self.servos[servo_id].is_mturn = is_mturn
		if interval is not None and interval != 0:

			interval = int(interval)             
			if is_mturn:
				if interval < t_acc + t_dec:
					interval = t_acc + t_dec
				elif interval > 4096000:
					interval = 4096000
				param_bytes = struct.pack('<BiIHHH', servo_id, angle, interval, t_acc, t_dec, power)
				self.send_request(self.CODE_SET_SERVO_ANGLE_MTURN_BY_INTERVAL, param_bytes)
			else:
				param_bytes = struct.pack('<BhHHHH', servo_id, angle, interval, t_acc, t_dec, power)
				self.send_request(self.CODE_SET_SERVO_ANGLE_BY_INTERVAL, param_bytes)
		elif velocity is not None:

			if velocity < 1.0:
				velocity = 1.0
			elif velocity > 750.0:
				velocity = 750.0
			velocity = int(velocity*10.0)
			
			if is_mturn:
				param_bytes = struct.pack('<BiHHHH', servo_id, angle, velocity, t_acc, t_dec, power)
				self.send_request(self.CODE_SET_SERVO_ANGLE_MTURN_BY_VELOCITY, param_bytes)
			else:
				param_bytes = struct.pack('<BhHHHH', servo_id, angle, velocity, t_acc, t_dec, power)
				self.send_request(self.CODE_SET_SERVO_ANGLE_BY_VELOCITY, param_bytes)
		else:

			if interval is None:
				# if srv_info.angle is None:
				srv_info.update(self.query_servo_angle(servo_id))
				interval = int((abs(angle*0.1 - srv_info.angle) / mean_dps) * 1000)
			if is_mturn:
				param_bytes = struct.pack('<BiIH', servo_id, angle, interval, power)
				self.send_request(self.CODE_SET_SERVO_ANGLE_MTURN, param_bytes)
			else:
				param_bytes = struct.pack('<BhHH', servo_id, angle, interval, power)
				self.send_request(self.CODE_SET_SERVO_ANGLE, param_bytes)

		
		
		return True
		
	def set_wheel(self, servo_id, mode, value=0, is_cw=True, mean_dps=None):
		'''设置舵机轮式模式控制
		@param servo_id
			舵机的ID号
		@param mode
			舵机的模式 取值范围[0,3]
		@param value 
			定时模式下代表时间(单位ms)
			定圈模式下代表圈数(单位圈)
		＠param is_cw
			轮子的旋转方向, is_cw代表是否是顺指针旋转
		@param speed
			轮子旋转的角速度, 单位 °/s
		'''
		method = mode | 0x80 if is_cw else mode
		mean_dps = self.mean_dps if mean_dps is None else mean_dps
		mean_dps = int(mean_dps)
		self.send_request(self.CODE_SET_SPIN, struct.pack('<BBHH', servo_id, method, mean_dps, value))
	
	def wheel_stop(self, servo_id):
		self.set_wheel(servo_id, self.WHEEL_MODE_STOP, 0, False, 0)
	
	def set_wheel_norm(self, servo_id, is_cw=True, mean_dps=None):
		self.set_wheel(servo_id, self.WHEEL_MODE_NORMAL, value=0, is_cw=is_cw, mean_dps=mean_dps)
		
	def set_wheel_turn(self, servo_id, turn=1, is_cw=True, mean_dps=None, is_wait=True):
		if mean_dps is None:
			mean_dps = self.mean_dps
		self.set_wheel(servo_id, self.WHEEL_MODE_TURN, value=turn, is_cw=is_cw, mean_dps=mean_dps)
		if is_wait:
			time.sleep(turn*360.0 / mean_dps)

	def set_wheel_time(self, servo_id, interval=1000, is_cw=True, mean_dps=None, is_wait=True):
		self.set_wheel(servo_id, self.WHEEL_MODE_TIME, value=interval, is_cw=is_cw, mean_dps=mean_dps)
		if is_wait:
			time.sleep(interval/1000.0)

	def set_damping(self, servo_id, power=0):
		'''设置阻尼模式
		@param servo_id
			舵机ID
		@param power
			舵机保持功率
		'''
		self.send_request(self.CODE_SET_DAMPING, struct.pack('<BH', servo_id, power))
	
	def reset_user_data(self, servo_id):
		self.send_request(self.CODE_RESET_USER_DATA, struct.pack('<B', servo_id))
		# self.update(wait_response=True)
		return True

	def response_reset_user_data(self, param_bytes):
		servo_id, result = struct.unpack('<BB', param_bytes)
		if self.is_debug:
			# logging.info("舵机用户数据重置 舵机ID={} 是否成功={}".format(servo_id, result))
			print("舵机用户数据重置 舵机ID={} 是否成功={}".format(servo_id, result))

	def read_data(self, servo_id, address):
		self.send_request(self.CODE_READ_DATA, struct.pack('<BB', servo_id, address))
		self.update(wait_response=True)
		if self.is_debug:
			logging.info("READ DATA 舵机ID={} Address={}".format(servo_id, address))
			logging.info("DATA : {}".format(self.servos[servo_id].data_table_raw_dict[address]))
		return self.servos[servo_id].data_table_raw_dict[address]

	def response_read_data(self, param_bytes):
		servo_id, address = struct.unpack('<BB', param_bytes[:2])
		content = param_bytes[2:]
		self.servos[servo_id].data_table_raw_dict[address] = content

	def write_data(self, servo_id, address, content):
		self.send_request(self.CODE_WRITE_DATA, struct.pack('<BB', servo_id, address)+content)
		self.servos[servo_id].data_write_success = False
		if self.is_debug:
			logging.info("WRITE DATA 舵机ID={} Address={} Value={}".format(servo_id, address, content))
		self.update(wait_response=True) 
		return self.servos[servo_id].data_write_success

	def response_write_data(self, param_bytes):
		servo_id, address, result = struct.unpack('<BBB', param_bytes)
		self.servos[servo_id].data_write_success = result == 1
		if self.is_debug:
			logging.info("WRITE DATA 舵机ID={} Address={} Result={}".format(servo_id, address, result))

	def query_voltage(self, servo_id):
		voltage_bytes = self.read_data(servo_id, self.ADDRESS_VOLTAGE)
		return struct.unpack('<H', voltage_bytes)[0] / 1000.0

	def query_current(self, servo_id):
		current_bytes = self.read_data(servo_id, self.ADDRESS_CURRENT)
		return struct.unpack('<H', current_bytes)[0] / 1000.0

	def query_power(self, servo_id):
		power_bytes = self.read_data(servo_id, self.ADDRESS_POWER)
		return struct.unpack('<H', power_bytes)[0] / 1000.0
	
	def query_temperature(self, servo_id):
		temp_bytes = self.read_data(servo_id, self.ADDRESS_TEMPERATURE)
		return float(struct.unpack('<H', temp_bytes)[0])

	def update(self, is_empty_buffer=False, wait_response=False, timeout=0.02):
		t_start = time.time() # 获取开始时间
		while True:
			buffer_bytes = self.uart.readall()
			
			if len(buffer_bytes) != 0:
				if self.is_debug:
					logging.info('Recv Bytes: ')
					logging.info(' '.join(['0x%02x'%b for b in buffer_bytes]))

			if buffer_bytes is not None:
				for b in buffer_bytes:
					self.pkt_buffer.update( struct.pack('<B', b))
			
			t_cur = time.time()
			is_timeout = (t_cur - t_start) > timeout
			
			if not wait_response:
				break
			elif self.pkt_buffer.has_valid_packet() or is_timeout:
				break
		

		while self.pkt_buffer.has_valid_packet():

			response_bytes = self.pkt_buffer.get_packet()

			code, param_bytes = Packet.unpack(response_bytes)

			if code in self.response_handle_funcs:
				self.response_handle_funcs[code](param_bytes)
			else:
				logging.warn('未知功能码 : {}'.format(code))

		if is_empty_buffer:
			self.pkt_buffer.empty_buffer()
		
	def is_stop(self):
		self.query_all_srv_angle()
		for servo_id, srv_info in self.servos.items():
			if not srv_info.is_stop():
				return False
		return True
	
	def wait(self, timeout=None):
		t_start = time.time()
		while True:
			self.query_all_srv_angle()
			if self.is_stop():
				break

			if timeout is not None:
				t_current = time.time()
				if t_current - t_start > timeout:
					break