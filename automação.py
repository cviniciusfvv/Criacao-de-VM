import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import re
import os

# Caminho padrão do VirtualBox no Windows
VBOX_PATH = r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"

class VBoxManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Painel Master VirtualBox - Gerenciador")
        self.root.geometry("950x880") # Aumentado para caber o campo de quantidade do clone
        
        if not os.path.exists(VBOX_PATH):
            messagebox.showerror("Erro Crítico", f"VBoxManage.exe não encontrado em:\n{VBOX_PATH}")
            self.root.destroy()
            return

        self.setup_ui()
        self.refresh_vms()

    def run_cmd(self, cmd_args):
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

        btn_start_vm = ttk.Button(left_frame, text="▶️ Iniciar VM Selecionada", command=self.iniciar_vm)
        btn_start_vm.pack(pady=5)

        # --- PAINEL DIREITO: ABAS DE CONTROLE ---
        right_frame = ttk.Frame(main_frame)
        main_frame.add(right_frame, weight=2)

        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.build_tab_redes()
        self.build_tab_hardware()
        self.build_tab_grupos()

    def refresh_vms(self):
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

            self.entry_vm_clone_src.delete(0, tk.END)
            self.entry_vm_clone_src.insert(0, vm_name)

    def iniciar_vm(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione uma VM na tabela para iniciar.")
            return
            
        vm_name = self.tree.item(selected[0], "values")[0]
        suc, out, err = self.run_cmd(["startvm", vm_name, "--type", "gui"])
        if not suc:
            messagebox.showerror("Erro", f"Falha ao iniciar a VM:\n{err}")

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
        if not vm: return

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
        if not vm: return

        inicio = int(self.spin_nic_start.get())
        qtd = int(self.spin_nic_qtd.get())

        for nic_num in range(inicio, inicio + qtd):
            self.run_cmd(["modifyvm", vm, f"--nic{nic_num}", "none"])
        messagebox.showinfo("Sucesso", "Placas removidas!")

    # ==========================================
    # ABA 2: HARDWARE E OPERAÇÕES
    # ==========================================
    def build_tab_hardware(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="💻 Hardware")

        # --- SEÇÃO: CRIAR VM ---
        lf_create = ttk.LabelFrame(tab, text="➕ Criar Nova Máquina Virtual (Lote)", padding=10)
        lf_create.pack(fill=tk.X, pady=2)

        ttk.Label(lf_create, text="Nome Base da VM:").grid(row=0, column=0, sticky="w")
        self.entry_new_vm = ttk.Entry(lf_create, width=30)
        self.entry_new_vm.grid(row=0, column=1, pady=2, sticky="w")

        ttk.Label(lf_create, text="Quantidade a criar:").grid(row=1, column=0, sticky="w")
        self.spin_vm_qtd = ttk.Spinbox(lf_create, from_=1, to=50, width=5)
        self.spin_vm_qtd.set(1)
        self.spin_vm_qtd.grid(row=1, column=1, pady=2, sticky="w")

        ttk.Label(lf_create, text="Sistema Operacional:").grid(row=2, column=0, sticky="w")
        self.cb_os = ttk.Combobox(lf_create, values=["Debian_64", "Windows10_64", "Windows2019_64", "Linux_64", "Ubuntu_64"], state="readonly")
        self.cb_os.set("Debian_64")
        self.cb_os.grid(row=2, column=1, pady=2, sticky="w")

        ttk.Label(lf_create, text="Memória RAM (MB):").grid(row=3, column=0, sticky="w")
        self.entry_new_ram = ttk.Entry(lf_create, width=15)
        self.entry_new_ram.insert(0, "2048")
        self.entry_new_ram.grid(row=3, column=1, pady=2, sticky="w")

        ttk.Label(lf_create, text="CPUs:").grid(row=4, column=0, sticky="w")
        self.entry_new_cpu = ttk.Entry(lf_create, width=15)
        self.entry_new_cpu.insert(0, "2")
        self.entry_new_cpu.grid(row=4, column=1, pady=2, sticky="w")

        ttk.Label(lf_create, text="Tamanho do HD (MB):").grid(row=5, column=0, sticky="w")
        self.entry_new_disk = ttk.Entry(lf_create, width=15)
        self.entry_new_disk.insert(0, "20000")
        self.entry_new_disk.grid(row=5, column=1, pady=2, sticky="w")

        ttk.Label(lf_create, text="Arquivo ISO:").grid(row=6, column=0, sticky="w")
        iso_frame = ttk.Frame(lf_create)
        iso_frame.grid(row=6, column=1, sticky="w", pady=2)
        
        self.entry_iso = ttk.Entry(iso_frame, width=30)
        self.entry_iso.pack(side=tk.LEFT)
        ttk.Button(iso_frame, text="Procurar...", command=self.procurar_iso).pack(side=tk.LEFT, padx=5)

        ttk.Button(lf_create, text="Criar Máquina(s) Virtual(is)", command=self.criar_vms_lote).grid(row=7, column=0, columnspan=2, pady=5)

        # --- SEÇÃO: CLONAR VM EM LOTE ---
        lf_clone = ttk.LabelFrame(tab, text="🐑 Clonar Máquina Virtual (Lote)", padding=10)
        lf_clone.pack(fill=tk.X, pady=2)

        ttk.Label(lf_clone, text="VM Origem (Selecione na tabela):").grid(row=0, column=0, sticky="w")
        self.entry_vm_clone_src = ttk.Entry(lf_clone, width=30)
        self.entry_vm_clone_src.grid(row=0, column=1, pady=2, sticky="w")

        ttk.Label(lf_clone, text="Nome Base do Clone:").grid(row=1, column=0, sticky="w")
        self.entry_vm_clone_dest = ttk.Entry(lf_clone, width=30)
        self.entry_vm_clone_dest.grid(row=1, column=1, pady=2, sticky="w")

        # NOVO CAMPO: Quantidade de Clones
        ttk.Label(lf_clone, text="Quantidade de Clones:").grid(row=2, column=0, sticky="w")
        self.spin_clone_qtd = ttk.Spinbox(lf_clone, from_=1, to=50, width=5)
        self.spin_clone_qtd.set(1)
        self.spin_clone_qtd.grid(row=2, column=1, pady=2, sticky="w")

        ttk.Button(lf_clone, text="Clonar e Gerar Novo(s) MAC(s)", command=self.clonar_vm).grid(row=3, column=0, columnspan=2, pady=5)

        # --- SEÇÃO: MODIFICAR VM ---
        lf_mod = ttk.LabelFrame(tab, text="⚙️ Modificar VM Existente", padding=10)
        lf_mod.pack(fill=tk.X, pady=2)

        ttk.Label(lf_mod, text="VM Alvo (Selecione na tabela):").grid(row=0, column=0, sticky="w")
        self.entry_vm_mod_hw = ttk.Entry(lf_mod, width=30)
        self.entry_vm_mod_hw.grid(row=0, column=1, pady=2, sticky="w")

        ttk.Label(lf_mod, text="Nova RAM (MB):").grid(row=1, column=0, sticky="w")
        self.entry_mod_ram = ttk.Entry(lf_mod, width=15)
        self.entry_mod_ram.grid(row=1, column=1, pady=2, sticky="w")

        ttk.Label(lf_mod, text="Novas CPUs:").grid(row=2, column=0, sticky="w")
        self.entry_mod_cpu = ttk.Entry(lf_mod, width=15)
        self.entry_mod_cpu.grid(row=2, column=1, pady=2, sticky="w")

        ttk.Button(lf_mod, text="Atualizar Hardware", command=self.aplicar_hardware).grid(row=3, column=0, columnspan=2, pady=5)

        # --- SEÇÃO: EXCLUIR VM ---
        lf_del = ttk.LabelFrame(tab, text="🗑️ Excluir Máquina Virtual", padding=10)
        lf_del.pack(fill=tk.X, pady=2)

        ttk.Label(lf_del, text="VM a Excluir:").grid(row=0, column=0, sticky="w")
        self.entry_vm_del_hw = ttk.Entry(lf_del, width=30)
        self.entry_vm_del_hw.grid(row=0, column=1, pady=2, sticky="w")

        ttk.Button(lf_del, text="🚨 Excluir VM Definitivamente", command=self.excluir_vm).grid(row=0, column=2, padx=10)

    def procurar_iso(self):
        caminho_iso = filedialog.askopenfilename(
            title="Selecione o arquivo ISO",
            filetypes=[("Arquivos ISO", "*.iso"), ("Todos os arquivos", "*.*")]
        )
        if caminho_iso:
            self.entry_iso.delete(0, tk.END)
            self.entry_iso.insert(0, caminho_iso)

    def criar_vms_lote(self):
        base_name = self.entry_new_vm.get().strip()
        qtd = int(self.spin_vm_qtd.get())
        os_type = self.cb_os.get()
        ram = self.entry_new_ram.get()
        cpu = self.entry_new_cpu.get()
        disk = self.entry_new_disk.get()
        iso_path = self.entry_iso.get().strip()

        if not base_name:
            messagebox.showwarning("Aviso", "Digite o nome base da VM.")
            return

        criadas = 0
        for i in range(1, qtd + 1):
            vm = f"{base_name}-{i}" if qtd > 1 else base_name

            suc, out, err = self.run_cmd(["createvm", "--name", vm, "--ostype", os_type, "--register"])
            if not suc:
                messagebox.showerror("Erro", f"Falha ao criar '{vm}':\n{err}")
                continue

            self.run_cmd(["modifyvm", vm, "--memory", ram, "--cpus", cpu, "--vram", "128", "--graphicscontroller", "vmsvga", "--boot1", "dvd", "--boot2", "disk", "--boot3", "none", "--boot4", "none"])
            self.run_cmd(["storagectl", vm, "--name", "SATA Controller", "--add", "sata", "--controller", "IntelAHCI"])
            
            vdi_dir = os.path.join(os.path.expanduser("~"), "VirtualBox VMs", vm)
            vdi_path = os.path.join(vdi_dir, f"{vm}.vdi")
            os.makedirs(vdi_dir, exist_ok=True) 

            self.run_cmd(["createmedium", "disk", "--filename", vdi_path, "--size", disk, "--format", "VDI"])
            self.run_cmd(["storageattach", vm, "--storagectl", "SATA Controller", "--port", "0", "--device", "0", "--type", "hdd", "--medium", vdi_path])
            
            if iso_path and os.path.exists(iso_path):
                self.run_cmd(["storageattach", vm, "--storagectl", "SATA Controller", "--port", "1", "--device", "0", "--type", "dvddrive", "--medium", iso_path])
            else:
                self.run_cmd(["storageattach", vm, "--storagectl", "SATA Controller", "--port", "1", "--device", "0", "--type", "dvddrive", "--medium", "emptydrive"])

            criadas += 1

        if criadas > 0:
            msg = f"Máquina '{base_name}' criada com sucesso!" if criadas == 1 else f"{criadas} máquinas criadas com sucesso!"
            messagebox.showinfo("Sucesso", msg)
            self.entry_new_vm.delete(0, tk.END)
            self.refresh_vms() 

    # Lógica Atualizada: Clonagem em Lote
    def clonar_vm(self):
        src_vm = self.entry_vm_clone_src.get().strip()
        base_dest_vm = self.entry_vm_clone_dest.get().strip()
        qtd = int(self.spin_clone_qtd.get())

        if not src_vm or not base_dest_vm:
            messagebox.showwarning("Aviso", "Preencha a VM de origem e o nome base do clone.")
            return

        clonadas = 0
        for i in range(1, qtd + 1):
            # Adiciona o sufixo -1, -2 etc, se for mais de um clone
            dest_vm = f"{base_dest_vm}-{i}" if qtd > 1 else base_dest_vm
            
            # O VirtualBox recria o MAC de todas as placas automaticamente ao omitir parâmetros de restrição
            suc, out, err = self.run_cmd(["clonevm", src_vm, "--name", dest_vm, "--register"])
            
            if not suc:
                messagebox.showerror("Erro", f"Falha ao clonar para '{dest_vm}':\n{err}")
                continue
            
            clonadas += 1

        if clonadas > 0:
            msg = f"Máquina '{src_vm}' clonada com sucesso para '{base_dest_vm}'!" if clonadas == 1 else f"{clonadas} clones gerados a partir de '{src_vm}' com novos MACs!"
            messagebox.showinfo("Sucesso", msg)
            self.entry_vm_clone_dest.delete(0, tk.END)
            self.refresh_vms()

    def aplicar_hardware(self):
        vm = self.entry_vm_mod_hw.get()
        ram = self.entry_mod_ram.get()
        cpu = self.entry_mod_cpu.get()

        if not vm: return
        if ram: self.run_cmd(["modifyvm", vm, "--memory", ram])
        if cpu: self.run_cmd(["modifyvm", vm, "--cpus", cpu])
        messagebox.showinfo("Sucesso", "Hardware atualizado!")
        self.entry_mod_ram.delete(0, tk.END)
        self.entry_mod_cpu.delete(0, tk.END)

    def excluir_vm(self):
        vm = self.entry_vm_del_hw.get().strip()
        if not vm: return

        resposta = messagebox.askyesno(
            "Confirmação Crítica", 
            f"Tem CERTEZA que deseja excluir a VM '{vm}' e todos os arquivos?"
        )
        if resposta:
            suc, out, err = self.run_cmd(["unregistervm", vm, "--delete"])
            if suc:
                messagebox.showinfo("Sucesso", f"Máquina '{vm}' excluída.")
                self.entry_vm_del_hw.delete(0, tk.END)
                self.refresh_vms()
            else:
                messagebox.showerror("Erro", f"Falha ao excluir:\n{err}")

    # ==========================================
    # ABA 3: GRUPOS
    # ==========================================
    def build_tab_grupos(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="📁 Grupos e Organização")

        ttk.Label(tab, text="VM Alvo:").grid(row=0, column=0, sticky="w")
        self.entry_vm_grupo = ttk.Entry(tab, width=30)
        self.entry_vm_grupo.grid(row=0, column=1, pady=5)

        ttk.Label(tab, text="Caminho do Grupo (Ex: /Testes/Redes):").grid(row=1, column=0, sticky="w")
        self.entry_grupo_path = ttk.Entry(tab, width=30)
        self.entry_grupo_path.grid(row=1, column=1, pady=5)

        ttk.Button(tab, text="Mover para Grupo", command=self.mover_grupo).grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(tab, text="Remover de Todos os Grupos (Raiz)", command=self.remover_grupo).grid(row=3, column=0, columnspan=2)

    def mover_grupo(self):
        vm = self.entry_vm_grupo.get()
        grupo = self.entry_grupo_path.get()
        if not vm or not grupo: return
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