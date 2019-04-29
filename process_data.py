import numpy as np
import pandas as pd
import re
import os
import glob
from difflib import get_close_matches
from openpyxl import load_workbook
import itertools
import sys
import datetime as dt



def process_file(path,company,report,history):
	sheets=[]
	cis=[]
	sites=[]
	all_sites=pd.DataFrame(columns=['Site*','Region','Site Group','City*'])
	for j in range(len(glob.glob(path+'/*'))):
		for k in range(len(pd.ExcelFile(glob.glob(path+'*')[j]).sheet_names)):
			sheets.append(pd.read_excel(glob.glob(path+'*')[j],pd.ExcelFile(glob.glob(path+'*')[j]).sheet_names[k]))     
		sheets[j].rename(columns=lambda x: x.strip().title(), inplace=True)
	for j in range(len(sheets)):
		###first overview prints####
		print('','#'*25,str(j+1)+': DATA TO BE VALIDATED '+ '#','#'*25,'',sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))		
		if len(os.listdir(path))==1:
			print(os.listdir(path)[0],'',sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))
		else:
			print(os.listdir(path)[j],'',sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))
		blank_cases=[]
		count_chars=[]
		null_columns=sheets[j][sheets[j].columns[sheets[j].isnull().any()]]  
				
		###blanks and char num
		for i in range(len(sheets[j].columns)):
			blank_cases.append(sheets[j].iloc[:,i][sheets[j].iloc[:,i].astype(str).apply(lambda x: x[0].isspace() or x[len(x)-1].isspace())].unique())
			count_chars.append(sheets[j].iloc[:,i].apply(lambda x: x if pd.isnull(x) else len(str(x))).max())
			sheets[j].iloc[:,i]=sheets[j].iloc[:,i].apply(lambda x: x.strip() if type(x)==str else x)
		##count max number of characteres per field
		chars=pd.concat([pd.Series(sheets[j].columns).rename('Field'),pd.Series(count_chars).rename('Number of Characters'),pd.Series(0*len(count_chars)).rename('Maximum allowed')],axis=1)
		#chars=chars.loc[:, chars.columns.notnull()]
		print('Number of records:'.upper(),'-'*len('Number of records:'), str(np.shape(sheets[j])[0]),'',
			'Field Names and Maximum number of Characteres per field:'.upper(),'-'*len('Field Names and Maximum number of Charactetrs per field:'),chars,'',sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))
		
		#print('Number of records:'.upper(),'-'*len('Number of records:'), str(np.shape(sheets[j])[0]),'','Field Names and Maximum number of Characteres per field:'.upper(),'-'*len('Field Names:'),pd.Series(sheets[j].columns),'',
		#	  sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))
		
		#check for blank spaces
		blanks=pd.concat([pd.Series(sheets[j].columns).rename('Field'),pd.Series(blank_cases).rename('Cases'),pd.Series(blank_cases).apply(lambda x: len(x)).rename('Count')],axis=1)
		if np.shape(blanks[blanks['Cases'].apply(lambda x: len(x)>0)])[0]>0:
			blank_spaces=blanks[blanks['Cases'].apply(lambda x: len(x)>0)]
		else:
			blank_spaces=str(0)
		print('Fields with blanks spaces:'.upper(),'-'*len('Fields with blanks spaces:'),blank_spaces,'',sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))
		
		if np.shape(null_columns.isnull().sum())[0]>0:
			null_fields=pd.DataFrame(null_columns.isnull().sum())
			null_fields.reset_index(level=0, inplace=True)
			null_fields.rename(columns={'index':'Field',0:'Count'},inplace=True)   
		else:
			null_fields=str(0)
		print('Fields with Null Values:'.upper(),'-'*len('Field with Null Values:'),null_fields,'',sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))

		###duplicated rows
		if np.shape(sheets[j][sheets[j].duplicated()])[0]>0:
			dup_rows=np.shape(sheets[j][sheets[j].duplicated()])[0]
		else:
			dup_rows=str(0)
		print('Number of Duplicated rows:'.upper(),'-'*len('Number of Duplicated rows:'),dup_rows,'',sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))
		sheets[j].drop_duplicates(inplace=True)
		####locations

		filtered_locations=sheets[j].filter(regex=re.compile('REG|GROUP|CITY',re.IGNORECASE))
		if np.shape(filtered_locations)[1]>0:
			print('Location values:'.upper(),sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))
			for k in range(np.shape(filtered_locations)[1]):    
				print('-'*len('Location values:'),filtered_locations.columns[k],filtered_locations.iloc[:,k].unique(),'',sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))
				if filtered_locations.iloc[:,k].str.isupper().any():
					#sheets[j][filtered_locations.columns[k]]=filtered_locations.iloc[:,k].apply(lambda x: x if pd.isnull(x) or type(x)==float or type(x)==int else x.title())
					print('Upper cases in ' + filtered_locations.columns[k],'',sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))
				else:
					None
		else:
			print('No location fields','-'*len('No location fields'))
		##############
		####ITSM sites
		#itsm_sites='/ITSM_sites'
		itsm_columns=['Site Name','Region','Site Group','City*+']
		print('All Existing Sites in CMDB:'.upper(),'-'*len('All Existing Sites in CMDB:'),sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))
		if len(glob.glob(history+'/*'))==0:
		#if len(glob.glob(company+itsm_sites+'/*'))==0:
			sites_itsm=pd.DataFrame(columns=itsm_columns)
			print('ITSM folder is empty','',sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))
		else:
			sites_itsm=pd.read_excel(glob.glob(history+'/*')[0],pd.ExcelFile(glob.glob(history+'/*')[0]).sheet_names[0])
			sites_itsm=sites_itsm[itsm_columns]
			print(np.shape(sites_itsm)[0],'',sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))                  
		###########################################################################################################################
		#SITES            
		if (~sheets[j].columns.str.contains('CI N',case=False).any()) & (sheets[j].columns.str.contains('SITE N|SITE+|SITE*',case=False).any()):
			all_sites=sheets[j].merge(sites_itsm.set_index(sites_itsm.columns[0]),left_on=sheets[j].filter(regex=re.compile('SITE',re.IGNORECASE)).columns[0],right_index=True,how='outer',indicator=True).drop_duplicates()
			###existing_sites##
			existing_sites=all_sites[all_sites['_merge']=='both'].iloc[:,:-1]
			###pick Site
			existing_sites=pd.concat([existing_sites.filter(regex=re.compile('SITE',re.IGNORECASE)).iloc[:,0],existing_sites.filter(regex=re.compile('REG|GROUP|CITY',re.IGNORECASE))],axis=1)
			existing_sites.rename(columns={
				existing_sites.filter(regex=re.compile('Region',re.IGNORECASE)).columns[0]:'Region in Sites',
				existing_sites.filter(regex=re.compile('Region',re.IGNORECASE)).columns[1]:'Region in ITSM Sites',
				existing_sites.filter(regex=re.compile('GROUP',re.IGNORECASE)).columns[0]:'Site Group in Sites',
				existing_sites.filter(regex=re.compile('GROUP',re.IGNORECASE)).columns[1]:'Site Group in ITSM Sites'},
				inplace=True)

			#wrong_locations_sites=existing_sites[existing_sites['Region_x']!=existing_sites['Region_y']].drop_duplicates().sort_values([existing_sites.columns[0]])
			
			#wrong_locations_sites=existing_sites[(existing_sites.filter(regex=re.compile('REG',re.IGNORECASE)).iloc[:,0])!=(existing_sites.filter(regex=re.compile('REG',re.IGNORECASE)).iloc[:,1]) | (existing_sites.filter(regex=re.compile('GROUP',re.IGNORECASE)).iloc[:,0])!=(existing_sites.filter(regex=re.compile('GROUP',re.IGNORECASE)).iloc[:,1])]          
			wrong_locations_sites=pd.concat([existing_sites[(existing_sites['Region in Sites'])!=(existing_sites['Region in ITSM Sites'])],existing_sites[(existing_sites['Site Group in Sites'])!=(existing_sites['Site Group in ITSM Sites'])]],axis=0).drop_duplicates()

			print('Sites with Wrong Region or Site Group when compared to existing sites in CMDB:'.upper(),'-'*len('Sites with Wrong Region or Site Group when compared to existing sites in CMDB:'),sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))
			wrong_locations_sites_list=[]
			if np.shape(wrong_locations_sites)[0]>0:
				print(np.shape(wrong_locations_sites)[0],'',sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))
				wrong_locations_sites_list.append(wrong_locations_sites)
			else:
				print('Region and Site Group are correct','',sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))     
			##new_sites###
			sites.append(sheets[j])
			if sites[0].columns.str.contains('Lon',case=False).any():
				sites[0]['Longitude']=sites[0].filter(regex=re.compile('Lon',re.IGNORECASE)).iloc[:,0].astype(str).apply(lambda x: re.findall(r'-?\d+\.?\d*', re.sub('[^A-Za-z0-9]+', '.',x))).apply(lambda x: ''.join(x) if len(x)>0 else 'NaN').astype(float)
			else:
				None
			if sites[0].columns.str.contains('Lat',case=False).any():
				sites[0]['Latitude']=sites[0].filter(regex=re.compile('Lat',re.IGNORECASE)).iloc[:,0].astype(str).apply(lambda x: re.findall(r'-?\d+\.?\d*', re.sub('[^A-Za-z0-9]+', '.',x))).apply(lambda x: ''.join(x) if len(x)>0 else 'NaN').astype(float)
			else:
				None
			#sites.append(all_sites[all_sites['_merge']!='right_only'].iloc[:,:-4])
			print('Sites to add in CMDB:'.upper(),'-'*len('Sites to add in CMDB:'),np.shape(sites[0])[0],'',sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))
			####duplicated sites
			sites_locations=pd.concat([sheets[j].filter(regex=re.compile('SITE',re.IGNORECASE)).iloc[:,0],sheets[j].filter(regex=re.compile('REG|GROUP|CITY',re.IGNORECASE))],axis=1)
			dup_sites=pd.DataFrame(sheets[j][pd.DataFrame(sites_locations.iloc[:,0]).duplicated(keep=False)].drop_duplicates()).sort_values([sites_locations.columns[0]])
			duplicate_sites=[]
			duplicate_sites.append(dup_sites.groupby(pd.DataFrame(sites_locations.iloc[:,0]).columns.values[0]).size().reset_index(name='counts'))
			if np.shape(duplicate_sites[0])[0]>0:
				duplicate_sites[0]
			elif np.shape(duplicate_sites[0])[0]==0:
				duplicate_sites[0]=str(0)
			else:
				duplicate_sites[0]='Wrong Site Name field'
			print('Duplicated Site Names (excluding duplicate rows):'.upper(),'-'*len('Duplicated Site Names (excluding duplicate rows):'),duplicate_sites[0],'',sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))  
		else:
			None
		#CIS
		if sheets[j].columns.str.contains('CI N',case=False).any():
			cis_locations=[]
			cis.append(sheets[j])
			site_name=cis[0][cis[0].columns[~cis[0].columns.str.contains('Group',case=False)].tolist()].filter(regex=re.compile('SITE',re.IGNORECASE))
			sites_reg=pd.concat([site_name,cis[0].filter(regex=re.compile('REG|GROUP',re.IGNORECASE))],axis=1).drop_duplicates()
			print(sites_reg['Region'].unique())
			#sites_reg=cis[0].filter(regex=re.compile('SITE N|SITE+|SITE*|REG|GROUP',re.IGNORECASE)).drop_duplicates()#merge(all_sites2.filter(regex=re.compile('SITE N|SITE+|SITE*|REG|GROUP|CITY',re.IGNORECASE)).set_index(all_sites2.columns[0]),left_on=cis[0].filter(regex=re.compile('SITE',re.IGNORECASE)).columns[0],right_index=True,how='inner',indicator=True).drop_duplicates()
			dup_sites_reg=sites_reg[sites_reg.iloc[:,0].duplicated(keep=False)].sort_values([sites_reg.columns[0]])
			print('Sites with multiple regions or Site Groups related in CIs data:'.upper(),'-'*len('Sites with multiple regions related in CIs data:'),sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))
			if np.shape(dup_sites_reg)[0]>0:
				cis_locations.append(dup_sites_reg)
				print(np.shape(dup_sites_reg)[0],'',sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))
			else:
				print('Site with correct region related:','',sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))
			filtered_cis=cis[0].filter(regex=re.compile('CI N',re.IGNORECASE))
			filtered_desc=cis[0].filter(regex=re.compile('DESC',re.IGNORECASE))
			filtered_region=cis[0].filter(regex=re.compile('REG',re.IGNORECASE))
			filtered_site_group=cis[0].filter(regex=re.compile('GROUP',re.IGNORECASE))
			filtered_dns=cis[0].filter(regex=re.compile('DNS',re.IGNORECASE))      
			if (np.shape(filtered_desc)[1]>0) & ((np.shape(filtered_region)[1]>0) | (np.shape(filtered_site_group)[1]>0)):
				with_region=(cis[0][filtered_desc.columns[0]]==cis[0][filtered_cis.columns[0]] + ' | ' + cis[0][filtered_region.columns[0]]).all()
				with_sitegroup=(cis[0][filtered_desc.columns[0]]==cis[0][filtered_cis.columns[0]] + ' | ' + cis[0][filtered_site_group.columns[0]]).all()
				well_conc=[with_region,with_sitegroup]
				if well_conc[0]==False:
					cis[0]['Suggested '+filtered_desc.columns[0]]=cis[0][filtered_cis.columns[0]] + ' | ' + cis[0][filtered_site_group.columns[0]]
				else:
					None
			else:
				well_conc='Missing or wrong name identifiers of the following fields: CI Name, CI Description, Region or Site Group'
			print('CI Description well concatenated:'.upper(),'-'*len('CI Description well concatenated:'),'With Region and Site Group:',well_conc,'',sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))
			###check concatenations -DNS
			if (np.shape(filtered_dns)[1]==1):
				well_conc_dns=(cis[0][filtered_dns.columns[0]]==cis[0][filtered_cis.columns[0]]).all()
				if well_conc_dns==False:
					cis[0][filtered_dns.columns[0]]=cis[0][filtered_cis.columns[0]]
				else:
					None
			else:
				well_conc_dns='Missing or wrong name identifiers of the following fields: CI Name, DNS Host Name'
			print('DNS Host Name has the same value as CI Name:'.upper(),'-'*len('DNS Host Name has the same value as CI Name:'),'With CI Name:',well_conc_dns,'',sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))       
			##duplicates
			duplicate_cis=[]
			dup_cis=pd.DataFrame(cis[0][filtered_cis.duplicated(keep=False)].drop_duplicates()).sort_values([filtered_cis.columns[0]])
			duplicate_cis.append(dup_cis.groupby(filtered_cis.columns.values[0]).size().reset_index(name='counts'))
			if np.shape(duplicate_cis[0])[0]>0:
				duplicate_cis[0]=duplicate_cis[0]
			elif np.shape(duplicate_cis[0])[0]==0:
				duplicate_cis[0]=str(0)
			else:
				duplicate_cis[0]='Wrong CI Name field'
			print('Duplicated CI Names (excluding duplicate rows):'.upper(),'-'*len('Duplicated CI Names (excluding duplicate rows):'),duplicate_cis[0],'',sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))
			#########################
			###product categorization
			opcat_template='Prod_Cats'
			if len(glob.glob(opcat_template+'/*'))==0:
				print('Prod Cat folder is empty','',sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))
				cis_list=[]
			else:
				template=pd.read_excel(glob.glob(opcat_template+'/*')[0],pd.ExcelFile(glob.glob(opcat_template+'/*')[0]).sheet_names[5])
				prodcats_cis=pd.concat([
				cis[0][cis[0].columns[~cis[0].columns.str.contains('Product N|Type',case=False)].tolist()].filter(regex=re.compile('Tier|Cat|Prod',re.IGNORECASE)),
				cis[0].filter(regex=re.compile('Product N',re.IGNORECASE)),
				cis[0].filter(regex=re.compile('Manuf',re.IGNORECASE))],axis=1)
				prodcats_cis.rename(columns={prodcats_cis.columns[3]:template.columns[3]},inplace=True)
				prod_missing=prodcats_cis.loc[~cis[0].filter(regex=re.compile('Product N',re.IGNORECASE)).iloc[:,0].isin(template.iloc[:,3])].drop_duplicates()
				prod_name=prod_missing.filter(regex=re.compile('Product N',re.IGNORECASE)).iloc[:,0]
				prod_match=prod_name.apply(lambda x: x if pd.isnull(x) or type(x)==float or type(x)==int else get_close_matches(x,template.iloc[:,3].astype(str).unique().tolist()))
				prod_suggested=prod_name.apply(lambda x: x if pd.isnull(x) or type(x)==float or type(x)==int else get_close_matches(x,template.iloc[:,3].astype(str).unique().tolist(),1)).apply(lambda x: x if pd.isnull(x) or type(x)==float or type(x)==int else ''.join(x))
				prod_missing_final=pd.concat([prod_missing,prod_suggested.rename('Suggested Product Name'),prod_match.rename('Others PN match')],axis=1)
				#wrong  product names tier classification
				same_prod=prodcats_cis.merge(template,left_on=prod_name.name,right_on=template.columns[3],how='inner').drop_duplicates()
				wrongcats1=same_prod.iloc[:,[0,5,3,4,8]][(same_prod.iloc[:,0]!=same_prod.iloc[:,5]) & (same_prod.iloc[:,1]==same_prod.iloc[:,6]) & (same_prod.iloc[:,2]==same_prod.iloc[:,7])].drop_duplicates()
				wrongcats2=same_prod.iloc[:,[1,6,3,4,8]][(same_prod.iloc[:,1]!=same_prod.iloc[:,6]) & (same_prod.iloc[:,0]==same_prod.iloc[:,5]) & (same_prod.iloc[:,2]==same_prod.iloc[:,7])].drop_duplicates()
				wrongcats3=same_prod.iloc[:,[2,7,3,4,8]][(same_prod.iloc[:,2]!=same_prod.iloc[:,7]) &(same_prod.iloc[:,0]==same_prod.iloc[:,5]) & (same_prod.iloc[:,1]==same_prod.iloc[:,6])].drop_duplicates()
				wrongcats1and2=same_prod.iloc[:,[0,5,1,6,3,4,8]][(same_prod.iloc[:,0]!=same_prod.iloc[:,5]) & (same_prod.iloc[:,1]!=same_prod.iloc[:,6]) & (same_prod.iloc[:,2]==same_prod.iloc[:,7])].drop_duplicates()
				wrongcats1and3=same_prod.iloc[:,[0,5,2,7,3,4,8]][(same_prod.iloc[:,0]!=same_prod.iloc[:,5]) & (same_prod.iloc[:,1]==same_prod.iloc[:,6]) & (same_prod.iloc[:,2]!=same_prod.iloc[:,7])].drop_duplicates()
				wrongcats2and3=same_prod.iloc[:,[1,6,2,7,3,4,8]][(same_prod.iloc[:,1]!=same_prod.iloc[:,6]) & (same_prod.iloc[:,2]!=same_prod.iloc[:,7]) & (same_prod.iloc[:,0]==same_prod.iloc[:,5])].drop_duplicates()
				wrongcats1and2and3=same_prod.iloc[:,[0,5,1,6,2,7,3,4,8]][(same_prod.iloc[:,0]!=same_prod.iloc[:,5]) & (same_prod.iloc[:,1]!=same_prod.iloc[:,6]) & (same_prod.iloc[:,2]!=same_prod.iloc[:,7])].drop_duplicates()
				wrong_manufacturer=same_prod.iloc[:,[3,4,8]][(same_prod.iloc[:,4]!=same_prod.iloc[:,8])].drop_duplicates()                        
				cis_list=[]
				cis_list.append(prod_missing_final)
				cis_list.append(wrongcats1)
				cis_list.append(wrongcats2)
				cis_list.append(wrongcats3)
				cis_list.append(wrongcats1and2)
				cis_list.append(wrongcats1and3)
				cis_list.append(wrongcats2and3)
				cis_list.append(wrongcats1and2and3)
				cis_list.append(wrong_manufacturer)
				issues_names=['Wrong product Name','Wrong Tier 1','Wrong Tier 2','Wrong Tier 3',
							  'Wrong Tier 1 and 2','Wrong Tier 1 and 3','Wrong Tier 2 and 3','Wrong Tier 1, 2 and 3',
							  'Wrong Manufacturer']
				issues=pd.concat([pd.Series(issues_names).rename('Field'),pd.Series(cis_list).apply(lambda x: len(x)).rename('COUNT')],axis=1)
				print('PRODUCT CATALOG ISSUES:','-'*len('PRODUCT CATALOG ISSUES:'),issues,'',sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))               
		else:
			None
	cis_sites_locations=[]
	if (len(cis)>0):
		if (len(sites)>0):
			conc_sites=[]
			for i in range(len(sites_itsm.columns)):
				conc_sites.append(pd.concat([sites_itsm.iloc[:,i],sites_locations.iloc[:,i]],axis=0))
			all_sites2=pd.concat(conc_sites,axis=1)
			all_sites2.rename(columns={
			all_sites2.columns[0]:'Site Name',
			all_sites2.columns[1]:'Region',
			all_sites2.columns[2]:'Site Group',
			all_sites2.columns[3]:'City'},inplace=True)
		else:
			#print('No Site File','',sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))
			all_sites2=sites_itsm
		existing_sites2=sites_reg.merge(all_sites2.filter(regex=re.compile('SITE N|SITE+|SITE*|REG|GROUP|CITY',re.IGNORECASE)).set_index(all_sites2.columns[0]),left_on=sites_reg.filter(regex=re.compile('SITE',re.IGNORECASE)).columns[0],right_index=True,how='inner').drop_duplicates()
		#new_sites=sites_reg.merge(all_sites2.filter(regex=re.compile('SITE N|SITE+|SITE*|REG|GROUP|CITY',re.IGNORECASE)).set_index(all_sites2.columns[0]),left_on=sites_reg.filter(regex=re.compile('SITE',re.IGNORECASE)).columns[0],right_index=True,how='outer',indicator=True).drop_duplicates()
		#new_sites=new_sites[new_sites['_merge']=='left_on']
		#existing_sites2=cis[0].filter(regex=re.compile('SITE N|SITE+|SITE*|REG|GROUP',re.IGNORECASE)).merge(all_sites2.filter(regex=re.compile('SITE N|SITE+|SITE*|REG|GROUP|CITY',re.IGNORECASE)).set_index(all_sites2.columns[0]),left_on=cis[0].filter(regex=re.compile('SITE',re.IGNORECASE)).columns[0],right_index=True,how='inner').drop_duplicates()
		existing_sites2.rename(columns={
			existing_sites2.filter(regex=re.compile('Region',re.IGNORECASE)).columns[0]:'Region in CIs',
			existing_sites2.filter(regex=re.compile('Region',re.IGNORECASE)).columns[1]:'Region in Sites',
			existing_sites2.filter(regex=re.compile('GROUP',re.IGNORECASE)).columns[0]:'Site Group in CIs',
			existing_sites2.filter(regex=re.compile('GROUP',re.IGNORECASE)).columns[1]:'Site Group in Sites'},inplace=True)

		#wrong_locations=existing_sites2[(existing_sites2['Region in CIs'])!=(existing_sites2['Region in Sites']) and (existing_sites2['Site Group in CIs'])!=(existing_sites2['Site Group in Sites'])].drop(['_merge'],axis=1)
		wrong_locations=pd.concat([existing_sites2[(existing_sites2['Region in CIs'])!=(existing_sites2['Region in Sites'])],existing_sites2[(existing_sites2['Site Group in CIs'])!=(existing_sites2['Site Group in Sites'])]],axis=0).drop_duplicates()

		#wrong_locations=existing_sites2[(existing_sites2.filter(regex=re.compile('GROUP',re.IGNORECASE)).iloc[:,0])!=(existing_sites2.filter(regex=re.compile('GROUP',re.IGNORECASE)).iloc[:,1])].drop(['_merge'],axis=1)
		
		print('Mismatched region for same Site Name between CIs data and Sites data:'.upper(),'-'*len('Mismatched region for same Site Name between CIs data and Sites data:'),sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))
		if np.shape(wrong_locations)[0]>0:
			cis_sites_locations.append(wrong_locations)
			#print(wrong_locations,'',sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))
			print('#: '+ str(np.shape(wrong_locations)[0]),'',sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))
		else:
			print('Region per site is the same in CIs data and Sites data',sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))
	else:
		None
		#print('NO CI File',sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))
	with pd.ExcelWriter(report + company + '_report_'+ dt.datetime.now().strftime("%Y-%m-%d %H-%M-%S") +'.xlsx',engine='xlsxwriter') as writer:
		print('','#################','#Report Overview#'.upper(),'#################','',sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))
		if len(sites)>0:
			sites[0].to_excel(writer, 'sites',index=False)
			if np.shape(dup_sites)[0]>0:
				dup_sites.to_excel(writer, 'Duplicate Sites',index=False)
			else:
				print('No Duplicate Sites',sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))
			if len(wrong_locations_sites_list)>0:
				wrong_locations_sites_list[0].to_excel(writer, 'Region Issues in Sites',index=False)
			else:
				print('No Wrong Locations in sites',sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))
		else:
			print('No Sites',sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))
		if len(cis)>0:
			cis[0].to_excel(writer, 'cis',index=False)
			if len(cis_locations)>0:
				cis_locations[0].to_excel(writer, 'Region Issues in CIs',index=False)
			else:
				print('No Wrong Locations in CIs',sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))
			if len(cis_sites_locations)>0:
				cis_sites_locations[0].to_excel(writer, 'CIs Sites Region Issues',index=False)   
			else:
				print('No Wrong locations between sites and cis',sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))    
			if np.shape(dup_cis)[0]>0:
				dup_cis.to_excel(writer, 'Duplicate CIs',index=False)
			else:
				print('No Duplicate CIs',sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))
			for i in range(len(cis_list)):
				if np.shape(cis_list[i])[0]>0:
					cis_list[i].to_excel(writer, issues_names[i],index=False)
				else:
					print('No ' + issues_names[i],sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))                       
		else:
			print('No CIs',sep='\n',file=open(report +'issues.txt','a',encoding='utf8'))
		writer.save()

