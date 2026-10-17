#ifndef __GUIGAME_H
#define __GUIGAME_H

#define SETTINGS_GLOBAL  0
#define SETTINGS_PERGAME 1

int guiGameAltStartupNameHandler(char *text, int maxLen);

char *gameConfigSource(void);

int guiGameVmcNameHandler(char *text, int maxLen);
void guiGameShowVMCMenu(int id, item_list_t *support);
void guiGameShowCompatConfig(int id, item_list_t *support, config_set_t *configSet);
void guiGameShowGSConfig(void);
void guiGameShowCheatConfig(void);

#ifdef PADEMU
void guiGameShowPadEmuConfig(int forceGlobal);
void guiGameShowPadMacroConfig(int forceGlobal);
void guiGameSavePadEmuGlobalConfig(config_set_t *configGame);
void guiGameSavePadMacroGlobalConfig(config_set_t *configGame);
void guiGameBtKeysPushToDriver(void);
void guiGameBtKeysRequestPush(void);
void guiGameBtKeysPushIfPending(void);
void guiGameBtKeysModuleArg(char *out); // needs BTKEYS_ARG_LEN bytes
void guiGameSetupModuleArg(unsigned char *out); // Controller Setup blob, PADSETUP_ARG_LEN bytes
void guiGameBtLedApply(int slot);               // send the lightbar colour of the slot to the menu driver
void guiGameBtLedOnConnect(int slot);           // a pad connected to the menu driver: apply its colour if the user chose one
int guiGameBtLedGet(int slot, unsigned char *rgb); // colour chosen for the slot, 0 = default
#endif

void guiGameShowOSDLanguageConfig(int forceGlobal);
void guiGameSaveOSDLanguageGlobalConfig(config_set_t *configGame);

void guiGameLoadConfig(item_list_t *support, config_set_t *configSet);
int guiGameSaveConfig(config_set_t *configSet, item_list_t *support);
void guiGameTestSettings(int id, item_list_t *support, config_set_t *configSet);

void guiGameRemoveSettings(config_set_t *configSet);
void guiGameRemoveGlobalSettings(config_set_t *configGame);
#endif
