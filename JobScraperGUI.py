import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading


from scraper.JobScarper_logic import setup_driver, login_to_site, scrape_jobs_for_export, write_jobs_to_csv # --- קבועים גלובליים ---



class JobScraperGUI(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Drushim Job Scraper")
        self.geometry("1100x900")
        self.driver = None
        self.scraper_thread = None

        #Style Configuration
        self.style = ttk.Style(self)
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TLabel', background='#f0f0f0', font=('Arial', 14))
        self.style.configure('TButton', font=('Arial', 14, 'bold'), padding=6)

        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="15 15 15 15")
        main_frame.pack(fill='both', expand=True)

        # HeadLine
        ttk.Label(main_frame, text="Welcome to Job Scarper", font=('Arial', 30, 'bold')).pack(pady=10)

        # Inputs frame
        input_frame = ttk.Frame(main_frame, padding="10", relief='groove', borderwidth=2)
        input_frame.pack(fill='x', pady=10)

        # 1.Username section
        ttk.Label(input_frame, text="User Name:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.username_var = tk.StringVar(value="")  
        self.username_entry = ttk.Entry(input_frame, textvariable=self.username_var, width=40)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5, sticky='e')

        # 2. Password section
        ttk.Label(input_frame, text="Password:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.password_var = tk.StringVar(value="")  
        self.password_entry = ttk.Entry(input_frame, textvariable=self.password_var, show='*', width=40)
        self.password_entry.grid(row=1, column=1, padx=5, pady=5, sticky='e')

        # 3.  Job_title section
        ttk.Label(input_frame, text="Job Title:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.job_title_var = tk.StringVar(value="Python Developer")
        self.job_title_entry = ttk.Entry(input_frame, textvariable=self.job_title_var, width=40)
        self.job_title_entry.grid(row=2, column=1, padx=5, pady=5, sticky='e')

        # 4. Location section
        ttk.Label(input_frame, text="Location:").grid(row=3, column=0, sticky='w', padx=5, pady=5)
        self.job_location_var = tk.StringVar(value="תל אביב")
        self.job_location_entry = ttk.Entry(input_frame, textvariable=self.job_location_var, width=40)
        self.job_location_entry.grid(row=3, column=1, padx=5, pady=5, sticky='e')

        # 5. Location section
        ttk.Label(input_frame, text="CSV file name:").grid(row=3, column=0, sticky='w', padx=5, pady=5)
        self.csv_file_name_var = tk.StringVar(value="job_results.csv")
        self.csv_file_name_entry = ttk.Entry(input_frame, textvariable=self.csv_file_name_var, width=40)
        self.csv_file_name_entry.grid(row=3, column=1, padx=5, pady=5, sticky='e')

        # 6.  Scraping limit section
        ttk.Label(input_frame, text="Scraping limit:").grid(row=4, column=0, sticky='w', padx=5, pady=5)
        self.limit_var = tk.IntVar(value=10)
        self.limit_entry = ttk.Entry(input_frame, textvariable=self.limit_var, width=40)
        self.limit_entry.grid(row=4, column=1, padx=5, pady=5, sticky='e')

        # Starrt button
        self.start_button = ttk.Button(main_frame, text="Start the Scraping", command=self.start_scraping_thread)
        self.start_button.pack(pady=10, fill='x')

        
        ttk.Label(main_frame, text=" Log messages:", font=('Arial', 14, 'bold')).pack(pady=(10, 5), anchor='w')
        self.status_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=15, width=70,
                                                     font=('Courier New', 9))
        self.status_text.pack(fill='both', expand=True)
        self.status_text.tag_config('error', foreground='red', font=('Courier New', 9, 'bold'))
        self.status_text.tag_config('success', foreground='green', font=('Courier New', 9, 'bold'))

    def log_message(self, message, tag=None):
        self.status_text.insert(tk.END, message + "\n", tag)
        self.status_text.see(tk.END)

    def start_scraping_thread(self):
        if self.scraper_thread and self.scraper_thread.is_alive():
            messagebox.showwarning("Working", "  Process begin .")
            return

        # GUI input's reading
        username = self.username_var.get()
        password = self.password_var.get()
        job_title = self.job_title_var.get()
        job_location = self.job_location_var.get()
        filename = self.csv_file_name_var.get()
        try:
            limit = self.limit_var.get()
        except tk.TclError:
            self.log_message("Please enter a valid limit number .", 'error')
            return

        # ניקוי יומן סטטוס והתחלת תהליך
        self.status_text.delete('1.0', tk.END)
        self.log_message("Starting the proccess")
        self.start_button.config(state=tk.DISABLED, text="...")

        # הפעלת הפונקציה הראשית בחוט נפרד
        self.scraper_thread = threading.Thread(
            target=self.main_scraper_process,
            args=(username, password, job_title, job_location, limit, filename)
        )
        self.scraper_thread.start()

    def main_scraper_process(self, username, password, job_title, job_location, limit, filename):
        try:
            self.driver = setup_driver(self.log_message)
            if not self.driver:
                return

            if not login_to_site(self.driver, username, password, job_title, job_location, self.log_message):
                self.log_message("Failed to connect ", 'error')
                return

            jobs_data = scrape_jobs_for_export(self.driver, limit, self.log_message)

            write_jobs_to_csv(jobs_data, filename, self.log_message)

            self.log_message('successfully ended')

        except Exception as e:
            self.log_message(f"Critical Error: {e}", 'error')
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
            # שחרור הכפתור ב-GUI
            self.start_button.config(state=tk.NORMAL, text="Start to scrap(CSV)")


if __name__ == "__main__":
    app = JobScraperGUI()
    app.mainloop()
