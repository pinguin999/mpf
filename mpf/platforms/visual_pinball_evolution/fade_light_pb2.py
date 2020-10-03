# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: fade_light.proto

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='fade_light.proto',
  package='',
  syntax='proto3',
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x10\x66\x61\x64\x65_light.proto\"\x98\x01\n\x10\x46\x61\x64\x65LightRequest\x12\x16\n\x0e\x63ommon_fade_ms\x18\x01 \x01(\r\x12,\n\x05\x66\x61\x64\x65s\x18\x02 \x03(\x0b\x32\x1d.FadeLightRequest.ChannelFade\x1a>\n\x0b\x43hannelFade\x12\x14\n\x0clight_number\x18\x01 \x01(\t\x12\x19\n\x11target_brightness\x18\x02 \x01(\x02\"\x8e\x01\n\x0e\x46\x61\x64\x65RGBRequest\x12\x14\n\x0clight_number\x18\x01 \x01(\t\x12\x1b\n\x13target_brightness_r\x18\x02 \x01(\x02\x12\x1b\n\x13target_brightness_g\x18\x03 \x01(\x02\x12\x1b\n\x13target_brightness_b\x18\x04 \x01(\x02\x12\x0f\n\x07\x66\x61\x64\x65_ms\x18\x05 \x01(\r\"Z\n\x16\x46\x61\x64\x65SingleColorRequest\x12\x14\n\x0clight_number\x18\x01 \x01(\t\x12\x19\n\x11target_brightness\x18\x02 \x01(\x02\x12\x0f\n\x07\x66\x61\x64\x65_ms\x18\x03 \x01(\r\"\x13\n\x11\x46\x61\x64\x65LightResponseb\x06proto3'
)




_FADELIGHTREQUEST_CHANNELFADE = _descriptor.Descriptor(
  name='ChannelFade',
  full_name='FadeLightRequest.ChannelFade',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='light_number', full_name='FadeLightRequest.ChannelFade.light_number', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='target_brightness', full_name='FadeLightRequest.ChannelFade.target_brightness', index=1,
      number=2, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=111,
  serialized_end=173,
)

_FADELIGHTREQUEST = _descriptor.Descriptor(
  name='FadeLightRequest',
  full_name='FadeLightRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='common_fade_ms', full_name='FadeLightRequest.common_fade_ms', index=0,
      number=1, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='fades', full_name='FadeLightRequest.fades', index=1,
      number=2, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[_FADELIGHTREQUEST_CHANNELFADE, ],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=21,
  serialized_end=173,
)


_FADERGBREQUEST = _descriptor.Descriptor(
  name='FadeRGBRequest',
  full_name='FadeRGBRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='light_number', full_name='FadeRGBRequest.light_number', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='target_brightness_r', full_name='FadeRGBRequest.target_brightness_r', index=1,
      number=2, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='target_brightness_g', full_name='FadeRGBRequest.target_brightness_g', index=2,
      number=3, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='target_brightness_b', full_name='FadeRGBRequest.target_brightness_b', index=3,
      number=4, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='fade_ms', full_name='FadeRGBRequest.fade_ms', index=4,
      number=5, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=176,
  serialized_end=318,
)


_FADESINGLECOLORREQUEST = _descriptor.Descriptor(
  name='FadeSingleColorRequest',
  full_name='FadeSingleColorRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='light_number', full_name='FadeSingleColorRequest.light_number', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='target_brightness', full_name='FadeSingleColorRequest.target_brightness', index=1,
      number=2, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='fade_ms', full_name='FadeSingleColorRequest.fade_ms', index=2,
      number=3, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=320,
  serialized_end=410,
)


_FADELIGHTRESPONSE = _descriptor.Descriptor(
  name='FadeLightResponse',
  full_name='FadeLightResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=412,
  serialized_end=431,
)

_FADELIGHTREQUEST_CHANNELFADE.containing_type = _FADELIGHTREQUEST
_FADELIGHTREQUEST.fields_by_name['fades'].message_type = _FADELIGHTREQUEST_CHANNELFADE
DESCRIPTOR.message_types_by_name['FadeLightRequest'] = _FADELIGHTREQUEST
DESCRIPTOR.message_types_by_name['FadeRGBRequest'] = _FADERGBREQUEST
DESCRIPTOR.message_types_by_name['FadeSingleColorRequest'] = _FADESINGLECOLORREQUEST
DESCRIPTOR.message_types_by_name['FadeLightResponse'] = _FADELIGHTRESPONSE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

FadeLightRequest = _reflection.GeneratedProtocolMessageType('FadeLightRequest', (_message.Message,), {

  'ChannelFade' : _reflection.GeneratedProtocolMessageType('ChannelFade', (_message.Message,), {
    'DESCRIPTOR' : _FADELIGHTREQUEST_CHANNELFADE,
    '__module__' : 'fade_light_pb2'
    # @@protoc_insertion_point(class_scope:FadeLightRequest.ChannelFade)
    })
  ,
  'DESCRIPTOR' : _FADELIGHTREQUEST,
  '__module__' : 'fade_light_pb2'
  # @@protoc_insertion_point(class_scope:FadeLightRequest)
  })
_sym_db.RegisterMessage(FadeLightRequest)
_sym_db.RegisterMessage(FadeLightRequest.ChannelFade)

FadeRGBRequest = _reflection.GeneratedProtocolMessageType('FadeRGBRequest', (_message.Message,), {
  'DESCRIPTOR' : _FADERGBREQUEST,
  '__module__' : 'fade_light_pb2'
  # @@protoc_insertion_point(class_scope:FadeRGBRequest)
  })
_sym_db.RegisterMessage(FadeRGBRequest)

FadeSingleColorRequest = _reflection.GeneratedProtocolMessageType('FadeSingleColorRequest', (_message.Message,), {
  'DESCRIPTOR' : _FADESINGLECOLORREQUEST,
  '__module__' : 'fade_light_pb2'
  # @@protoc_insertion_point(class_scope:FadeSingleColorRequest)
  })
_sym_db.RegisterMessage(FadeSingleColorRequest)

FadeLightResponse = _reflection.GeneratedProtocolMessageType('FadeLightResponse', (_message.Message,), {
  'DESCRIPTOR' : _FADELIGHTRESPONSE,
  '__module__' : 'fade_light_pb2'
  # @@protoc_insertion_point(class_scope:FadeLightResponse)
  })
_sym_db.RegisterMessage(FadeLightResponse)


# @@protoc_insertion_point(module_scope)
