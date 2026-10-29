from fpdf import FPDF

class PolicyReport(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 15)
        self.set_text_color(30, 58, 138)
        self.cell(0, 10, 'Republic of South Africa - National Treasury', border=False, ln=1, align='C')
        self.set_font('helvetica', 'I', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, 'Macroeconomic Twin: Cabinet Memorandum & Simulation Data', border=False, ln=1, align='C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_pdf(ai_text, df_scenario, df_baseline, levers):
    pdf = PolicyReport()
    pdf.add_page()
    
    pdf.set_font('helvetica', 'B', 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, '1. Economic Advisory Memo', ln=1)
    
    pdf.set_font('helvetica', '', 10)
    clean_text = ai_text.replace('**', '').replace('###', '').replace('*', '-')
    pdf.multi_cell(0, 6, clean_text)
    pdf.ln(10)
    
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 10, '2. Policy Levers Applied', ln=1)
    pdf.set_font('helvetica', '', 10)
    
    lever_text = f"VAT Rate: {levers.get('vat', 15)}% | Corporate Tax: {levers.get('cit', 27)}% | Personal Tax: {levers.get('pit', 30)}%\n"
    lever_text += f"B-BBEE Redirect: {levers.get('bbbee', 10)}% | Tariffs: {levers.get('tariff', 0)}% | Localization: {levers.get('localization', 0)}%\n"
    pdf.multi_cell(0, 6, lever_text)
    pdf.ln(5)

    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 10, '3. 5-Year Macroeconomic Projection', ln=1)
    
    pdf.set_font('helvetica', 'B', 9)
    pdf.set_fill_color(240, 240, 240)
    col_width = 38
    pdf.cell(col_width, 8, 'Year', border=1, fill=True, align='C')
    pdf.cell(col_width, 8, 'GDP (R Trillion)', border=1, fill=True, align='C')
    pdf.cell(col_width, 8, 'Debt-to-GDP (%)', border=1, fill=True, align='C')
    pdf.cell(col_width, 8, 'Jobs Created', border=1, fill=True, align='C')
    pdf.cell(col_width, 8, 'Net Fiscal (R mn)', border=1, fill=True, align='C')
    pdf.ln()
    
    pdf.set_font('helvetica', '', 9)
    for _, row in df_scenario.iterrows():
        pdf.cell(col_width, 8, str(row['Year']), border=1, align='C')
        pdf.cell(col_width, 8, f"{row['GDP']:.2f}", border=1, align='C')
        pdf.cell(col_width, 8, f"{row['Debt_to_GDP']:.1f}%", border=1, align='C')
        pdf.cell(col_width, 8, f"{row['Jobs_Created']:,.0f}", border=1, align='C')
        pdf.cell(col_width, 8, f"{row['Net_Fiscal_mn']:,.0f}", border=1, align='C')
        pdf.ln()

    pdf.ln(10)
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 10, '4. Baseline Comparison (Year 5)', ln=1)
    pdf.set_font('helvetica', '', 10)
    
    scen_y5 = df_scenario.iloc[-1]
    base_y5 = df_baseline.iloc[-1]
    
    diff_gdp = scen_y5['GDP'] - base_y5['GDP']
    diff_debt = scen_y5['Debt_to_GDP'] - base_y5['Debt_to_GDP']
    
    comp_text = f"Under this scenario, Year 5 GDP is R{diff_gdp:+.2f} Trillion compared to the baseline.\n"
    comp_text += f"The Debt-to-GDP ratio is {diff_debt:+.1f} percentage points compared to the baseline.\n"
    pdf.multi_cell(0, 6, comp_text)

    return bytes(pdf.output())
