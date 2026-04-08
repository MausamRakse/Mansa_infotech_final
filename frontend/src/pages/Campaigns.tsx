import React, { useState, useEffect } from 'react';
import { Upload, Download, Calendar, Clock, Globe, Rocket, HelpCircle, FileSpreadsheet, CheckCircle2, ChevronRight, AlertCircle, Trash2, Settings as SettingsIcon } from 'lucide-react';
import * as XLSX from 'xlsx';
import { listAgents, createCampaign, type Agent } from '../api/client';
import toast from 'react-hot-toast';

const Campaigns = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [previewData, setPreviewData] = useState<any[]>([]);
  
  const [formData, setFormData] = useState({
    campaign_name: '',
    agent_id: '',
    start_time: '09:00',
    end_time: '18:00',
    time_zone: 'IST',
    custom_first_line: 'Hey, am I speaking with {name}?',
    retries: '1'
  });

  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    try {
      const data = await listAgents();
      setAgents(data);
    } catch (error) {
      toast.error('Failed to load agents');
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (evt) => {
      try {
        const bstr = evt.target?.result;
        const wb = XLSX.read(bstr, { type: 'binary' });
        const wsname = wb.SheetNames[0];
        const ws = wb.Sheets[wsname];
        const data = XLSX.utils.sheet_to_json(ws);
        setPreviewData(data);
        toast.success(`Loaded ${data.length} contacts from Excel`);
      } catch (err) {
        toast.error('Failed to parse Excel file');
      }
    };
    reader.readAsBinaryString(file);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.agent_id) return toast.error('Please select an agent');
    if (previewData.length === 0) return toast.error('Please upload a contact list');

    try {
      setSubmitting(true);
      const response = await createCampaign({
        campaign_name: formData.campaign_name,
        agent_id: formData.agent_id,
        start_time: formData.start_time,
        end_time: formData.end_time,
        time_zone: formData.time_zone,
        custom_first_line: formData.custom_first_line
      });

      console.log('Campaign Created:', response);
      toast.success('Campaign created successfully!');
    } catch (error) {
      toast.error('Failed to create campaign');
    } finally {
      setSubmitting(false);
    }
  };

  const timeZones = [
    "IST", "UTC", "GMT", "EST", "PST", "CST", "MST", "AST", "PKT", "BST",
    "ICT", "JST", "KST", "AEST", "ACST", "AWST", "NZST"
  ];

  return (
    <div className="max-w-6xl mx-auto pb-20">
      <div className="mb-8">
        <h1 className="text-[28px] font-bold text-textPrimary mb-2">Create New Campaign</h1>
        <p className="text-textMuted text-[16px]">Connect with thousands of customers in hours rather than days.</p>
      </div>

      <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Configuration */}
        <div className="lg:col-span-2 space-y-8">
          
          {/* Section 1: Campaign Details */}
          <div className="bg-white rounded-[20px] p-8 border border-border shadow-sm">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-primary-light flex items-center justify-center text-primary">
                <Rocket className="w-5 h-5" />
              </div>
              <h2 className="text-[18px] font-semibold">Campaign Details</h2>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-[14px] font-medium text-textPrimary">Campaign Name</label>
                <input
                  type="text"
                  required
                  placeholder="Enter Campaign Name"
                  className="w-full h-12 px-4 rounded-xl border border-border focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all"
                  value={formData.campaign_name}
                  onChange={(e) => setFormData({...formData, campaign_name: e.target.value})}
                />
              </div>

              <div className="space-y-2">
                <label className="text-[14px] font-medium text-textPrimary">Select Voice Agent</label>
                <select
                  required
                  className="w-full h-12 px-4 rounded-xl border border-border focus:border-primary focus:ring-1 focus:ring-primary outline-none bg-white transition-all appearance-none"
                  value={formData.agent_id}
                  onChange={(e) => setFormData({...formData, agent_id: e.target.value})}
                >
                  <option value="">Select an Agent</option>
                  {agents.map((a: Agent) => <option key={a.id} value={a.id}>{a.name}</option>)}
                </select>
              </div>
            </div>
          </div>

          {/* Section 2: Contact List */}
          <div className="bg-white rounded-[20px] p-8 border border-border shadow-sm">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-primary-light flex items-center justify-center text-primary">
                  <FileSpreadsheet className="w-5 h-5" />
                </div>
                <h2 className="text-[18px] font-semibold">Contact List</h2>
              </div>
              <a href="#" className="text-primary text-[14px] hover:underline flex items-center gap-1 font-medium">
                <Download className="w-4 h-4" />
                Download Template
              </a>
            </div>

            <div className={`
              border-2 border-dashed rounded-[20px] p-10 flex flex-col items-center gap-4 transition-all
              ${previewData.length > 0 ? 'border-success-light bg-success-light/5' : 'border-border hover:border-primary/50'}
            `}>
              <div className="w-12 h-12 rounded-full bg-surface flex items-center justify-center text-textMuted">
                <Upload className="w-6 h-6" />
              </div>
              <div className="text-center">
                <p className="font-semibold text-[16px]">Contact List (Excel file)</p>
                <p className="text-textMuted text-[14px]">Drag and drop your spreadsheet here or click to browse</p>
              </div>
              <input
                type="file"
                accept=".xlsx, .xls"
                onChange={handleFileUpload}
                className="hidden"
                id="excel-upload"
              />
              <label
                htmlFor="excel-upload"
                className="px-6 py-2.5 bg-surface text-textPrimary border border-border rounded-lg hover:bg-white hover:shadow-sm transition-all cursor-pointer font-medium text-[14px]"
              >
                {previewData.length > 0 ? 'Change File' : 'Choose File'}
              </label>
            </div>

            {previewData.length > 0 && (
              <div className="mt-8 overflow-hidden rounded-xl border border-border">
                <div className="bg-surface px-4 py-3 border-b border-border flex items-center justify-between">
                  <span className="text-[14px] font-semibold">{previewData.length} contacts found</span>
                  <button 
                    type="button" 
                    onClick={() => setPreviewData([])}
                    className="text-error hover:text-error-dark transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
                <div className="overflow-x-auto max-h-[300px]">
                  <table className="w-full text-left text-[13px]">
                    <thead className="bg-surface sticky top-0">
                      <tr>
                        {Object.keys(previewData[0]).map(key => (
                          <th key={key} className="px-4 py-2 font-semibold border-b border-border capitalize">{key}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {previewData.slice(0, 5).map((row: any, i: number) => (
                        <tr key={i} className="border-b border-border hover:bg-surface/50">
                          {Object.values(row).map((val: any, j: number) => (
                            <td key={j} className="px-4 py-2">{val}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {previewData.length > 5 && (
                    <div className="p-4 text-center text-textMuted italic bg-surface/30">
                      And {previewData.length - 5} more contacts...
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Section 3: Settings & Schedule */}
          <div className="bg-white rounded-[20px] p-8 border border-border shadow-sm">
             <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                <div className="space-y-6">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-primary-light flex items-center justify-center text-primary">
                      <SettingsIcon className="w-5 h-5" />
                    </div>
                    <h2 className="text-[18px] font-semibold">Campaign Settings</h2>
                  </div>
                  
                  <div className="space-y-4">
                    <div className="space-y-2">
                       <label className="text-[14px] font-medium text-textPrimary flex items-center gap-2">
                        Select Retries
                        <HelpCircle className="w-3.5 h-3.5 text-textMuted" />
                      </label>
                      <select
                        className="w-full h-12 px-4 rounded-xl border border-border outline-none bg-white font-medium focus:ring-1 focus:ring-primary"
                        value={formData.retries}
                        onChange={(e) => setFormData({...formData, retries: e.target.value})}
                      >
                        <option value="0">No Retries</option>
                        <option value="1">1 Retry</option>
                        <option value="2">2 Retries</option>
                        <option value="3">3 Retries</option>
                      </select>
                      <p className="text-[12px] text-textMuted">Select the times you want Convexa to retry unpicked calls.</p>
                    </div>

                    <div className="space-y-2">
                      <label className="text-[14px] font-medium text-textPrimary">Custom First Line</label>
                      <textarea
                        placeholder="Hey, am I speaking with {name}?"
                        className="w-full h-24 p-4 rounded-xl border border-border outline-none focus:ring-1 focus:ring-primary resize-none"
                        value={formData.custom_first_line}
                        onChange={(e) => setFormData({...formData, custom_first_line: e.target.value})}
                      />
                    </div>
                  </div>
                </div>

                <div className="space-y-6">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-primary-light flex items-center justify-center text-primary">
                      <Calendar className="w-5 h-5" />
                    </div>
                    <h2 className="text-[18px] font-semibold">Schedule</h2>
                  </div>

                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                       <div className="space-y-2">
                        <label className="text-[14px] font-medium text-textPrimary flex items-center gap-2">
                          Start Time <Clock className="w-3.5 h-3.5 text-textMuted" />
                        </label>
                        <input
                          type="time"
                          className="w-full h-12 px-4 rounded-xl border border-border outline-none font-medium focus:ring-1 focus:ring-primary"
                          value={formData.start_time}
                          onChange={(e) => setFormData({...formData, start_time: e.target.value})}
                        />
                      </div>
                      <div className="space-y-2">
                        <label className="text-[14px] font-medium text-textPrimary flex items-center gap-2">
                          End Time <Clock className="w-3.5 h-3.5 text-textMuted" />
                        </label>
                        <input
                          type="time"
                          className="w-full h-12 px-4 rounded-xl border border-border outline-none font-medium focus:ring-1 focus:ring-primary"
                          value={formData.end_time}
                          onChange={(e) => setFormData({...formData, end_time: e.target.value})}
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <label className="text-[14px] font-medium text-textPrimary flex items-center gap-2">
                        Time Zone <Globe className="w-3.5 h-3.5 text-textMuted" />
                      </label>
                      <select
                        className="w-full h-12 px-4 rounded-xl border border-border outline-none bg-white font-medium focus:ring-1 focus:ring-primary"
                        value={formData.time_zone}
                        onChange={(e) => setFormData({...formData, time_zone: e.target.value})}
                      >
                        {timeZones.map(tz => <option key={tz} value={tz}>{tz}</option>)}
                      </select>
                    </div>
                  </div>
                </div>
             </div>
          </div>
        </div>

        {/* Right Column: Sticky Summary & Action */}
        <div className="lg:col-span-1">
          <div className="sticky top-8 space-y-6">
            <div className="bg-white rounded-[20px] p-8 border border-border shadow-md">
              <h3 className="text-[18px] font-bold mb-6">Launch Summary</h3>
              
              <div className="space-y-4 mb-8">
                <div className="flex items-start gap-3">
                  <CheckCircle2 className={`w-5 h-5 mt-0.5 ${formData.campaign_name ? 'text-success' : 'text-textMuted opacity-50'}`} />
                  <div className="flex-1">
                    <p className="text-[14px] font-medium">Campaign Configured</p>
                    <p className="text-[12px] text-textMuted">{formData.campaign_name || 'Missing name'}</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <CheckCircle2 className={`w-5 h-5 mt-0.5 ${previewData.length > 0 ? 'text-success' : 'text-textMuted opacity-50'}`} />
                  <div className="flex-1">
                    <p className="text-[14px] font-medium">Contacts Processed</p>
                    <p className="text-[12px] text-textMuted">{previewData.length} contacts staged</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <CheckCircle2 className={`w-5 h-5 mt-0.5 ${formData.agent_id ? 'text-success' : 'text-textMuted opacity-50'}`} />
                  <div className="flex-1">
                    <p className="text-[14px] font-medium">Agent Selected</p>
                    <p className="text-[12px] text-textMuted">{agents.find((a: Agent) => a.id === formData.agent_id)?.name || 'None selected'}</p>
                  </div>
                </div>
              </div>

              <button
                disabled={submitting}
                className={`
                  w-full py-4 rounded-xl font-bold text-[16px] flex items-center justify-center gap-2 transition-all
                  ${submitting 
                    ? 'bg-primary/50 cursor-not-allowed' 
                    : 'bg-primary text-white hover:bg-primary-dark hover:scale-[1.02] active:scale-[0.98] shadow-lg shadow-primary/20'}
                `}
              >
                {submitting ? (
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <>
                    Create Campaign
                    <ChevronRight className="w-5 h-5" />
                  </>
                )}
              </button>

              <div className="mt-6 flex items-start gap-3 p-4 bg-surface rounded-xl">
                 <AlertCircle className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                 <p className="text-[12px] text-textMuted">
                   Launching will sync your contact list with Tabbly and schedule outreach immediately.
                 </p>
              </div>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
};

export default Campaigns;
