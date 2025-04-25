from bleak import BleakClient, BleakScanner
from config import CHARACTERISTIC_UUID

class BLEController:
    def __init__(self):
        self.client = None

    async def scan(self):
        devices = await BleakScanner.discover()
        return [(d.name, d.address) for d in devices if d.name]

    async def connect(self, address):
        self.client = BleakClient(address)
        await self.client.connect()
        return self.client.is_connected

    async def disconnect(self):
        if self.client and self.client.is_connected:
            await self.client.disconnect()

    async def send_command(self, hex_command):
        if self.client and self.client.is_connected:
            await self.client.write_gatt_char(CHARACTERISTIC_UUID, bytes.fromhex(hex_command))
