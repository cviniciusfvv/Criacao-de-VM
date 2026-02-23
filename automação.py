import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import re
import os

# Caminho padrão do VirtualBox no Windows
VBOX_PATH = r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"

class VBoxManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Painel Master VirtualBox - [CAMPINAS TECH]")
        self.root.geometry("950x700") # Aumentei um pouco a altura para caber a nova opção
        
        # Valida se o VBoxManage existe
        if not os.path.exists(VBOX_PATH):
            messagebox.showerror("Erro Crítico", f"VBoxManage.exe não encontrado em:\n{VBOX_PATH}")
            self.root.destroy()
            return

        self.setup_ui()
        self.refresh_vms()

    def run_cmd(self, cmd_args):
        """Executa comandos do VirtualBox sem abrir a tela preta do CMD"""
        comando_completo = [VBOX_PATH] + cmd_args
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        try:
            result = subprocess.run(
                comando_completo, 
                capture_output=True, 
                text=True, 
                startupinfo=startupinfo
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)

    def setup_ui(self):
        # Frame Principal
        main_frame = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- PAINEL ESQUERDO: TABELA DE VMs ---
        left_frame = ttk.LabelFrame(main_frame, text="Máquinas Virtuais Registradas")
        main_frame.add(left_frame, weight=1)

        columns = ("Nome", "UUID")
        self.tree = ttk.Treeview(left_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("Nome", text="Nome da VM")
        self.tree.heading("UUID", text="Identificador")
        self.tree.column("Nome", width=220)
        self.tree.column("UUID", width=80)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.tree.bind("<<TreeviewSelect>>", self.on_vm_select)

        btn_refresh = ttk.Button(left_frame, text="🔄 Atualizar Lista", command=self.refresh_vms)
        btn_refresh.pack(pady=5)

        # --- PAINEL DIREITO: ABAS DE CONTROLE ---
        right_frame = ttk.Frame(main_frame)
        main_frame.add(right_frame, weight=2)

        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.build_tab_redes()
        self.build_tab_hardware()
        self.build_tab_grupos()

    def refresh_vms(self):
        """Busca as VMs no VirtualBox e atualiza a tabela gráfica"""
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        success, stdout, stderr = self.run_cmd(["list", "vms"])
        if success:
            pattern = re.compile(r'"([^"]+)"\s+\{(.+)\}')
            for line in stdout.splitlines():
                match = pattern.match(line)
                if match:
                    nome, uuid = match.groups()
                    self.tree.insert("", tk.END, values=(nome, uuid))

    def on_vm_select(self, event):
        """Preenche os campos automaticamente ao clicar na tabela"""
        selected = self.tree.selection()
        if selected:
            vm_name = self.tree.item(selected[0], "values")[0]
            
            self.entry_vm_rede.delete(0, tk.END)
            self.entry_vm_rede.insert(0, vm_name)
            
            self.entry_vm_mod_hw.delete(0, tk.END)
            self.entry_vm_mod_hw.insert(0, vm_name)

            self.entry_vm_del_hw.delete(0, tk.END)
            self.entry_vm_del_hw.insert(0, vm_name)
            
            self.entry_vm_grupo.delete(0, tk.END)
            self.entry_vm_grupo.insert(0, vm_name)

    # ==========================================
    # ABA 1: REDES
    # ==========================================
    def build_tab_redes(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="🌐 Redes")

        ttk.Label(tab, text="VM Alvo (Selecione na tabela):").grid(row=0, column=0, sticky="w")
        self.entry_vm_rede = ttk.Entry(tab, width=30)
        self.entry_vm_rede.grid(row=0, column=1, pady=5, sticky="w")

        ttk.Label(tab, text="Placa Inicial (1-8):").grid(row=1, column=0, sticky="w")
        self.spin_nic_start = ttk.Spinbox(tab, from_=1, to=8, width=5)
        self.spin_nic_start.set(1)
        self.spin_nic_start.grid(row=1, column=1, pady=5, sticky="w")

        ttk.Label(tab, text="Qtd. de Placas a Configurar/Remover:").grid(row=2, column=0, sticky="w")
        self.spin_nic_qtd = ttk.Spinbox(tab, from_=1, to=8, width=5)
        self.spin_nic_qtd.set(1)
        self.spin_nic_qtd.grid(row=2, column=1, pady=5, sticky="w")

        ttk.Label(tab, text="Modo de Conexão:").grid(row=3, column=0, sticky="w", pady=10)
        self.var_modo = tk.StringVar(value="nat")
        modos_frame = ttk.Frame(tab)
        modos_frame.grid(row=3, column=1, sticky="w")
        ttk.Radiobutton(modos_frame, text="NAT", variable=self.var_modo, value="nat").pack(side=tk.LEFT)
        ttk.Radiobutton(modos_frame, text="Bridge", variable=self.var_modo, value="bridged").pack(side=tk.LEFT)
        ttk.Radiobutton(modos_frame, text="Interna", variable=self.var_modo, value="intnet").pack(side=tk.LEFT)

        ttk.Label(tab, text="Nome da Rede Interna:").grid(row=4, column=0, sticky="w")
        self.entry_rede_int = ttk.Entry(tab, width=20)
        self.entry_rede_int.insert(0, "vlan10")
        self.entry_rede_int.grid(row=4, column=1, pady=5, sticky="w")

        ttk.Label(tab, text="Modo Promíscuo:").grid(row=5, column=0, sticky="w", pady=10)
        self.var_promisc = tk.StringVar(value="deny")
        promisc_frame = ttk.Frame(tab)
        promisc_frame.grid(row=5, column=1, sticky="w")
        ttk.Radiobutton(promisc_frame, text="Negar", variable=self.var_promisc, value="deny").pack(side=tk.LEFT)
        ttk.Radiobutton(promisc_frame, text="Permitir VMs", variable=self.var_promisc, value="allow-vms").pack(side=tk.LEFT)
        ttk.Radiobutton(promisc_frame, text="All (Sniffing)", variable=self.var_promisc, value="allow-all").pack(side=tk.LEFT)

        btn_frame = ttk.Frame(tab)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text="✅ Configurar Placas", command=self.aplicar_redes).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="🗑️ Remover Placas", command=self.remover_redes).pack(side=tk.LEFT, padx=10)

    def aplicar_redes(self):
        vm = self.entry_vm_rede.get()
        if not vm:
            messagebox.showwarning("Aviso", "Selecione uma VM primeiro.")
            return

        inicio = int(self.spin_nic_start.get())
        qtd = int(self.spin_nic_qtd.get())
        modo = self.var_modo.get()
        promisc = self.var_promisc.get()
        rede_int = self.entry_rede_int.get()

        for nic_num in range(inicio, inicio + qtd):
            args = ["modifyvm", vm, f"--nic{nic_num}", modo]
            if modo == "intnet":
                args.extend([f"--intnet{nic_num}", rede_int])
            self.run_cmd(args)
            self.run_cmd(["modifyvm", vm, f"--nicpromisc{nic_num}", promisc])
        
        messagebox.showinfo("Sucesso", f"Redes da VM '{vm}' configuradas!")

    def remover_redes(self):
        vm = self.entry_vm_rede.get()
        if not vm:
            messagebox.showwarning("Aviso", "Selecione uma VM primeiro.")
            return

        inicio = int(self.spin_nic_start.get())
        qtd = int(self.spin_nic_qtd.get())

        for nic_num in range(inicio, inicio + qtd):
            self.run_cmd(["modifyvm", vm, f"--nic{nic_num}", "none"])
        
        fim = inicio + qtd - 1
        msg = f"Placa {inicio} removida!" if qtd == 1 else f"Placas de {inicio} até {fim} removidas!"
        messagebox.showinfo("Sucesso", f"{msg}\n(VM: {vm})")

    # ==========================================
    # ABA 2: HARDWARE
    # ==========================================
    def build_tab_hardware(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="💻 Hardware")

        # --- SEÇÃO: CRIAR VM ---
        lf_create = ttk.LabelFrame(tab, text="➕ Criar Nova Máquina Virtual", padding=10)
        lf_create.pack(fill=tk.X, pady=5)

        ttk.Label(lf_create, text="Nome da Nova VM:").grid(row=0, column=0, sticky="w")
        self.entry_new_vm = ttk.Entry(lf_create, width=30)
        self.entry_new_vm.grid(row=0, column=1, pady=2, sticky="w")

        ttk.Label(lf_create, text="Sistema Operacional:").grid(row=1, column=0, sticky="w")
        self.cb_os = ttk.Combobox(lf_create, values=["Debian_64", "Windows10_64", "Windows2019_64", "Linux_64"], state="readonly")
        self.cb_os.set("Debian_64")
        self.cb_os.grid(row=1, column=1, pady=2, sticky="w")

        ttk.Label(lf_create, text="Memória RAM (MB):").grid(row=2, column=0, sticky="w")
        self.entry_new_ram = ttk.Entry(lf_create, width=15)
        self.entry_new_ram.insert(0, "2048")
        self.entry_new_ram.grid(row=2, column=1, pady=2, sticky="w")

        ttk.Label(lf_create, text="Quantidade de CPUs:").grid(row=3, column=0, sticky="w")
        self.entry_new_cpu = ttk.Entry(lf_create, width=15)
        self.entry_new_cpu.insert(0, "2")
        self.entry_new_cpu.grid(row=3, column=1, pady=2, sticky="w")

        ttk.Label(lf_create, text="Tamanho do HD (MB):").grid(row=4, column=0, sticky="w")
        self.entry_new_disk = ttk.Entry(lf_create, width=15)
        self.entry_new_disk.insert(0, "20000")
        self.entry_new_disk.grid(row=4, column=1, pady=2, sticky="w")

        ttk.Button(lf_create, text="Criar Máquina Virtual", command=self.criar_vm).grid(row=5, column=0, columnspan=2, pady=10)

        # --- SEÇÃO: MODIFICAR VM ---
        lf_mod = ttk.LabelFrame(tab, text="⚙️ Modificar VM Existente", padding=10)
        lf_mod.pack(fill=tk.X, pady=5)

        ttk.Label(lf_mod, text="VM Alvo:").grid(row=0, column=0, sticky="w")
        self.entry_vm_mod_hw = ttk.Entry(lf_mod, width=30)
        self.entry_vm_mod_hw.grid(row=0, column=1, pady=5, sticky="w")

        ttk.Label(lf_mod, text="Nova RAM (MB):").grid(row=1, column=0, sticky="w")
        self.entry_mod_ram = ttk.Entry(lf_mod, width=15)
        self.entry_mod_ram.grid(row=1, column=1, pady=5, sticky="w")

        ttk.Label(lf_mod, text="Novas CPUs:").grid(row=2, column=0, sticky="w")
        self.entry_mod_cpu = ttk.Entry(lf_mod, width=15)
        self.entry_mod_cpu.grid(row=2, column=1, pady=5, sticky="w")

        ttk.Button(lf_mod, text="Atualizar Hardware", command=self.aplicar_hardware).grid(row=3, column=0, columnspan=2, pady=10)

        # --- SEÇÃO: EXCLUIR VM ---
        lf_del = ttk.LabelFrame(tab, text="🗑️ Excluir Máquina Virtual", padding=10)
        lf_del.pack(fill=tk.X, pady=5)

        ttk.Label(lf_del, text="VM a Excluir:").grid(row=0, column=0, sticky="w")
        self.entry_vm_del_hw = ttk.Entry(lf_del, width=30)
        self.entry_vm_del_hw.grid(row=0, column=1, pady=5, sticky="w")

        ttk.Button(lf_del, text="🚨 Excluir VM Definitivamente", command=self.excluir_vm).grid(row=0, column=2, padx=10)

    def criar_vm(self):
        vm = self.entry_new_vm.get().strip()
        os_type = self.cb_os.get()
        ram = self.entry_new_ram.get()
        cpu = self.entry_new_cpu.get()
        disk = self.entry_new_disk.get()

        if not vm:
            messagebox.showwarning("Aviso", "Digite o nome da nova VM.")
            return

        suc, out, err = self.run_cmd(["createvm", "--name", vm, "--ostype", os_type, "--register"])
        if not suc:
            messagebox.showerror("Erro", f"Falha ao criar (O nome já existe?):\n{err}")
            return

        self.run_cmd(["modifyvm", vm, "--memory", ram, "--cpus", cpu, "--vram", "128", "--graphicscontroller", "vmsvga", "--boot1", "dvd", "--boot2", "disk", "--boot3", "none", "--boot4", "none"])
        self.run_cmd(["storagectl", vm, "--name", "SATA Controller", "--add", "sata", "--controller", "IntelAHCI"])
        
        vdi_dir = os.path.join(os.path.expanduser("~"), "VirtualBox VMs", vm)
        vdi_path = os.path.join(vdi_dir, f"{vm}.vdi")
        os.makedirs(vdi_dir, exist_ok=True) 

        self.run_cmd(["createmedium", "disk", "--filename", vdi_path, "--size", disk, "--format", "VDI"])
        self.run_cmd(["storageattach", vm, "--storagectl", "SATA Controller", "--port", "0", "--device", "0", "--type", "hdd", "--medium", vdi_path])
        self.run_cmd(["storageattach", vm, "--storagectl", "SATA Controller", "--port", "1", "--device", "0", "--type", "dvddrive", "--medium", "emptydrive"])

        messagebox.showinfo("Sucesso", f"Máquina '{vm}' criada e pronta para uso!")
        self.entry_new_vm.delete(0, tk.END)
        self.refresh_vms() 

    def aplicar_hardware(self):
        vm = self.entry_vm_mod_hw.get()
        ram = self.entry_mod_ram.get()
        cpu = self.entry_mod_cpu.get()

        if not vm:
            messagebox.showwarning("Aviso", "Selecione uma VM.")
            return

        if ram: self.run_cmd(["modifyvm", vm, "--memory", ram])
        if cpu: self.run_cmd(["modifyvm", vm, "--cpus", cpu])
        
        messagebox.showinfo("Sucesso", "Hardware atualizado!")
        self.entry_mod_ram.delete(0, tk.END)
        self.entry_mod_cpu.delete(0, tk.END)

    def excluir_vm(self):
        """Função para excluir completamente a VM e seus arquivos"""
        vm = self.entry_vm_del_hw.get().strip()
        
        if not vm:
            messagebox.showwarning("Aviso", "Selecione a VM que deseja excluir.")
            return

        # Caixa de diálogo de confirmação crítica
        resposta = messagebox.askyesno(
            "Confirmação Crítica", 
            f"Tem CERTEZA que deseja excluir a VM '{vm}'?\n\nIsso apagará o disco virtual (.vdi) e TODOS os arquivos irremediavelmente."
        )
        
        if resposta:
            suc, out, err = self.run_cmd(["unregistervm", vm, "--delete"])
            if suc:
                messagebox.showinfo("Sucesso", f"Máquina '{vm}' foi excluída e todos os arquivos removidos.")
                self.entry_vm_del_hw.delete(0, tk.END)
                self.refresh_vms() # Atualiza a tabela imediatamente
            else:
                messagebox.showerror("Erro", f"Falha ao excluir a VM:\n{err}")

    # ==========================================
    # ABA 3: GRUPOS
    # ==========================================
    def build_tab_grupos(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="📁 Grupos e Organização")

        ttk.Label(tab, text="VM Alvo:").grid(row=0, column=0, sticky="w")
        self.entry_vm_grupo = ttk.Entry(tab, width=30)
        self.entry_vm_grupo.grid(row=0, column=1, pady=5)

        ttk.Label(tab, text="Caminho do Grupo (Ex: /Lab/Kali):").grid(row=1, column=0, sticky="w")
        self.entry_grupo_path = ttk.Entry(tab, width=30)
        self.entry_grupo_path.grid(row=1, column=1, pady=5)

        ttk.Button(tab, text="Mover para Grupo", command=self.mover_grupo).grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(tab, text="Remover de Todos os Grupos (Raiz)", command=self.remover_grupo).grid(row=3, column=0, columnspan=2)

    def mover_grupo(self):
        vm = self.entry_vm_grupo.get()
        grupo = self.entry_grupo_path.get()
        
        if not vm or not grupo:
            messagebox.showwarning("Aviso", "Preencha a VM e o caminho do grupo.")
            return
            
        if not grupo.startswith("/"): grupo = "/" + grupo
            
        success, out, err = self.run_cmd(["modifyvm", vm, "--groups", grupo])
        if success:
            messagebox.showinfo("Sucesso", f"VM movida para {grupo}")
        else:
            messagebox.showerror("Erro", f"Falha ao mover:\n{err}")

    def remover_grupo(self):
        vm = self.entry_vm_grupo.get()
        if not vm: return
        self.run_cmd(["modifyvm", vm, "--groups", "/"])
        messagebox.showinfo("Sucesso", "VM retornou para a raiz.")

if __name__ == "__main__":
    root = tk.Tk()
    app = VBoxManagerApp(root)
    root.mainloop()