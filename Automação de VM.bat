@echo off
setlocal enabledelayedexpansion
title Painel Master VirtualBox v11.0 - [CAMPINAS TECH]

:: ===================================================
:: INICIALIZACAO
:: ===================================================
set "VBOX_PATH=C:\Program Files\Oracle\VirtualBox"
if not exist "!VBOX_PATH!\VBoxManage.exe" (
    echo [ERRO CRITICO] VirtualBox nao encontrado.
    echo Caminho procurado: "!VBOX_PATH!"
    pause
    exit
)
cd /d "!VBOX_PATH!"

:MENU_PRINCIPAL
cls
echo ===================================================
echo        PAINEL DE CONTROLE - LABORATORIO
echo ===================================================
echo.
echo  [1] REDES (NAT, Bridge, Promiscuo, Sniffing)
echo  [2] HARDWARE (Criar VM, Aumentar RAM/CPU)
echo  [3] ORGANIZACAO (Criar Grupos e Subgrupos)
echo  [4] SAIR
echo.
set "MENU_OPT="
set /p "MENU_OPT=Escolha uma opcao (1-4): "

:: Sistema de redirecionamento seguro
if "!MENU_OPT!"=="1" goto SEC_REDES
if "!MENU_OPT!"=="2" goto SEC_HARDWARE
if "!MENU_OPT!"=="3" goto SEC_GRUPOS
if "!MENU_OPT!"=="4" exit
goto MENU_PRINCIPAL

:: =============================================================================================
:: SECAO 1: REDES
:: =============================================================================================
:SEC_REDES
cls
echo --- CONFIGURACAO DE REDE ---
echo.
VBoxManage list vms
echo.

set "ACAO=1"
set /p "ACAO=[1] Configurar Placas  [2] Remover Placas  [3] Voltar: "
if "!ACAO!"=="3" goto MENU_PRINCIPAL

set "MODO=nat"
set "REDE_INT=intnet"
set "PROMISC=deny"

if "!ACAO!"=="2" set "MODO=none"
if "!ACAO!"=="2" goto PULAR_CONFIG_REDE

echo.
echo [1] NAT  [2] Bridge  [3] Rede Interna  [4] Host-Only
set /p "T=Escolha o Modo (1-4): "
if "!T!"=="2" set "MODO=bridged"
if "!T!"=="3" set "MODO=intnet"
if "!T!"=="4" set "MODO=hostonly"

if "!MODO!"=="intnet" set /p "REDE_INT=Nome da Rede Interna (Ex: vlan10): "

echo.
echo Promiscuo (Sniffing): [1] Deny  [2] Allow-VMs  [3] Allow-All
set /p "P=Escolha (1-3): "
if "!P!"=="2" set "PROMISC=allow-vms"
if "!P!"=="3" set "PROMISC=allow-all"

:PULAR_CONFIG_REDE
echo.
set "V_QTD=1"
set "N_QTD=1"
set "S_NIC=1"

set /p "V_QTD=Quantas VMs serao alteradas? (Padrao 1): "
set /p "N_QTD=Quantas placas por VM? (Padrao 1): "
set /p "S_NIC=Comecar por qual placa (1-8)? (Padrao 1): "

:: Chama sub-rotina de calculo
call :PROCESSAR_CALCULO_REDE !V_QTD! !N_QTD! !S_NIC!
echo.
echo [INFO] Configuracao de rede finalizada.
pause
goto MENU_PRINCIPAL

:: =============================================================================================
:: SECAO 2: HARDWARE
:: =============================================================================================
:SEC_HARDWARE
cls
echo --- GESTAO DE HARDWARE ---
echo.
echo [1] Criar Nova Maquina Virtual
echo [2] Modificar Hardware (RAM/CPU)
echo [3] Voltar
echo.
set "HW_OPT="
set /p "HW_OPT=Escolha (1-3): "

if "!HW_OPT!"=="1" goto HW_CRIAR
if "!HW_OPT!"=="2" goto HW_MODIFICAR
if "!HW_OPT!"=="3" goto MENU_PRINCIPAL
goto SEC_HARDWARE

:HW_CRIAR
cls
echo --- CRIANDO NOVA VM ---
echo.
set "VM_NAME="
set /p "VM_NAME=Nome da Nova VM (Sem espacos, ou 0 para voltar): "
if "!VM_NAME!"=="" goto SEC_HARDWARE
if "!VM_NAME!"=="0" goto SEC_HARDWARE

set "OS_TYPE=Debian_64"
echo [1] Linux (Debian/Kali/VyOS) [2] Win10 [3] WinServer
set /p "OS_OPT=OS (Padrao 1): "
if "!OS_OPT!"=="2" set "OS_TYPE=Windows10_64"
if "!OS_OPT!"=="3" set "OS_TYPE=Windows2019_64"

set "RAM_SIZE=2048"
set "CPU_COUNT=2"
set "DISK_SIZE=20000"

set /p "RAM_SIZE=Memoria RAM (Padrao 2048): "
set /p "CPU_COUNT=CPUs (Padrao 2): "
set /p "DISK_SIZE=Disco HD em MB (Padrao 20000): "

echo [PROCESSANDO] Construindo !VM_NAME!...
VBoxManage createvm --name "!VM_NAME!" --ostype "!OS_TYPE!" --register
VBoxManage modifyvm "!VM_NAME!" --memory !RAM_SIZE! --cpus !CPU_COUNT! --vram 128 --graphicscontroller vmsvga --boot1 dvd --boot2 disk --boot3 none --boot4 none
VBoxManage storagectl "!VM_NAME!" --name "SATA Controller" --add sata --controller IntelAHCI

set "VDI_PATH=C:\Users\%USERNAME%\VirtualBox VMs\!VM_NAME!\!VM_NAME!.vdi"
VBoxManage createmedium disk --filename "!VDI_PATH!" --size !DISK_SIZE! --format VDI
VBoxManage storageattach "!VM_NAME!" --storagectl "SATA Controller" --port 0 --device 0 --type hdd --medium "!VDI_PATH!"
VBoxManage storageattach "!VM_NAME!" --storagectl "SATA Controller" --port 1 --device 0 --type dvddrive --medium emptydrive

echo [OK] VM Criada!
pause
goto MENU_PRINCIPAL

:HW_MODIFICAR
cls
echo --- MODIFICAR VM EXISTENTE ---
echo.
VBoxManage list vms
echo.
set "VM_MOD_NAME="
set /p "VM_MOD_NAME=Nome da VM (ou 0 para voltar): "
if "!VM_MOD_NAME!"=="" goto SEC_HARDWARE
if "!VM_MOD_NAME!"=="0" goto SEC_HARDWARE

set "NOVA_RAM="
set "NOVA_CPU="
echo Deixe em branco para nao alterar.
set /p "NOVA_RAM=Nova RAM (MB): "
set /p "NOVA_CPU=Novas CPUs: "

if not "!NOVA_RAM!"=="" VBoxManage modifyvm "!VM_MOD_NAME!" --memory !NOVA_RAM!
if not "!NOVA_CPU!"=="" VBoxManage modifyvm "!VM_MOD_NAME!" --cpus !NOVA_CPU!

echo [OK] Hardware atualizado!
pause
goto MENU_PRINCIPAL

:: =============================================================================================
:: SECAO 3: ORGANIZADOR DE GRUPOS (ESTRUTURA LINEAR)
:: =============================================================================================
:SEC_GRUPOS
cls
echo --- ORGANIZADOR DE GRUPOS ---
echo.
echo [1] Mover VM para Grupo (Ex: /Lab/Kali)
echo [2] Remover VM de Grupo (Voltar para Raiz)
echo [3] Voltar
echo.
set "GP_OPT="
set /p "GP_OPT=Escolha (1-3): "

if "!GP_OPT!"=="1" goto GP_MOVER
if "!GP_OPT!"=="2" goto GP_REMOVER
if "!GP_OPT!"=="3" goto MENU_PRINCIPAL
goto SEC_GRUPOS

:GP_MOVER
cls
echo --- MOVER PARA GRUPO ---
echo.
VBoxManage list vms
echo.
set "VM_ALVO="
set /p "VM_ALVO=Nome da VM (ou 0 para voltar): "
if "!VM_ALVO!"=="" goto SEC_GRUPOS
if "!VM_ALVO!"=="0" goto SEC_GRUPOS

set "NOVO_GRUPO="
echo Exemplo: /MeusLabs/Seguranca
set /p "NOVO_GRUPO=Caminho do Grupo: "

:: Logica linear (sem parenteses) para evitar fechar sozinho
if "!NOVO_GRUPO!"=="" goto SEC_GRUPOS
if not "!NOVO_GRUPO:~0,1!"=="/" set "NOVO_GRUPO=/!NOVO_GRUPO!"

echo Movendo "!VM_ALVO!" para "!NOVO_GRUPO!"...
VBoxManage modifyvm "!VM_ALVO!" --groups "!NOVO_GRUPO!"
echo [OK] Operacao tentada.
pause
goto MENU_PRINCIPAL

:GP_REMOVER
cls
echo --- REMOVER GRUPO (VOLTAR A RAIZ) ---
echo.
VBoxManage list vms
echo.
set "VM_ALVO="
set /p "VM_ALVO=Nome da VM (ou 0 para voltar): "
if "!VM_ALVO!"=="" goto SEC_GRUPOS
if "!VM_ALVO!"=="0" goto SEC_GRUPOS

echo Resetando grupo da VM...
VBoxManage modifyvm "!VM_ALVO!" --groups "/"
echo [OK] Feito.
pause
goto MENU_PRINCIPAL

:: =============================================================================================
:: SUB-ROTINAS DE SISTEMA
:: =============================================================================================
:PROCESSAR_CALCULO_REDE
set /a "total_vms=%1"
set /a "total_nics=%2"
set /a "start_nic=%3"
set /a "fim_nic=start_nic + total_nics - 1"

echo.
echo CONFIGURANDO PLACAS: !start_nic! ate !fim_nic!
echo ---------------------------------------------------

for /l %%i in (1,1,!total_vms!) do (
    echo.
    set "VM_NAME="
    set /p "VM_NAME=Nome da VM #%%i (Case Sensitive): "
    
    if not "!VM_NAME!"=="" (
        for /l %%n in (!start_nic!,1,!fim_nic!) do (
            if "!ACAO!"=="1" (
                echo [OK] !VM_NAME! Placa %%n -^> !MODO!
                if "!MODO!"=="intnet" (
                    VBoxManage modifyvm "!VM_NAME!" --nic%%n intnet --intnet%%n "!REDE_INT!"
                ) else (
                    VBoxManage modifyvm "!VM_NAME!" --nic%%n !MODO!
                )
                VBoxManage modifyvm "!VM_NAME!" --nicpromisc%%n !PROMISC!
            ) else (
                echo [REMOVIDO] !VM_NAME! Placa %%n
                VBoxManage modifyvm "!VM_NAME!" --nic%%n none
            )
        )
    )
)
exit /b