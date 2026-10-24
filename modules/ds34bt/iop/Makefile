IOP_BIN = ds34bt.irx
IOP_OBJS = ds34bt.o smsutils.o imports.o

IOP_INCS += -I../../../include/

# Debug builds log the dongle and pad link state (BT: lines, see BTDBG in ds34bt.c). BT_DEBUG=2 adds the verbose HCI lines.
ifeq ($(DEBUG),1)
IOP_CFLAGS += -DBT_DEBUG=$(if $(BT_VERBOSE),2,1)
endif

include $(PS2SDK)/Defs.make
include ../../Rules.bin.make
include $(PS2SDK)/samples/Makefile.iopglobal
