# PostgreSQL & pgAdmin Setup Guide

## DB SETUP

Step 1) Install PostgreSQL which will include pgAdmin (a GUI with which you are able to modify databases)

Step 2) Run pgAdmin

![image](https://user-images.githubusercontent.com/15320504/157739536-b83af6e8-b64c-4f60-bacd-ed2230d3caa6.png)

Step 3) pgAdmin will ask for your master password on open: this is set in the installation

![image](https://user-images.githubusercontent.com/15320504/157739561-c974462c-ef3f-4c64-bcee-ae2b7eb86eaa.png)

Step 4) Within the navigation panel on the left, click the arrow beside Servers. Now, you may be prompted to input a personal user password (although this wasn't necessarily the case for all users) 

![image](https://user-images.githubusercontent.com/15320504/157739612-dfefd2a6-02ad-4743-a3ef-c209b51cc942.png)

Step 5) Right click on Databases -> Create -> Database. For this local installation, I used ‘dbGen’ as the name.

![image](https://user-images.githubusercontent.com/15320504/157739658-cf04e493-6434-46dc-af89-5067441073a5.png)

This should be all you need to setup the initial DB

## ACCESSING & MODIFYING DATA

To view/edit table data, click the dropdown arrow beside the dbGen database, and then the dropdown arrow beside Schemas, and finally the dropdown arrow beside ‘public’ (this is the default schema provided by Postgres).

![image](https://user-images.githubusercontent.com/15320504/157739748-8d09eb1b-ab88-49eb-81e1-f0f40556b0cb.png)

Here, you can see your tables (if any exist) and modify them. If you right click a table, you can modify its fields/info in Properties, or records in View/Edit Data.

![image](https://user-images.githubusercontent.com/15320504/157739804-ddb5a310-fa4f-4701-8ea5-c903796f073d.png)

Properties menu (important columns noted)

![image](https://user-images.githubusercontent.com/15320504/157739830-1bf8e2ef-c376-4382-ba4c-39f913d04949.png)

Using the table in the View/Edit Data menu, you can manually add or adjust record data. Unsaved changes will appear as bolded text within the table, make sure you press F6 to save the changes you make.

![image](https://user-images.githubusercontent.com/15320504/157739940-f974fed5-97e7-4e0f-81bb-248c3e09fbdf.png)
