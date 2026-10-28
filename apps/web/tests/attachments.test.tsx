import React from 'react';
import {render,screen,cleanup} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {it,expect,afterEach,vi} from 'vitest';
import AttachmentsPanel from '../app/console/AttachmentsPanel';
afterEach(cleanup);
it('shows authorized download links without upload controls to viewers',async()=>{
 const api=vi.fn(async()=>[{id:'f',filename:'evidence.txt',size:10,internal:false}]);
 render(<AttachmentsPanel api={api} kind="support" target="ticket" canWrite={false}/>);
 expect((await screen.findByRole('link')).getAttribute('href')).toBe('/api/files/support/ticket/f');
 expect(screen.queryByLabelText('Text evidence file')).toBeNull();
});
it('uploads decoded text and refreshes persisted attachments',async()=>{
 let saved=false;const api=vi.fn(async(p:string,m?:string)=>{if(m==='POST'){saved=true;return {id:'f'}}return saved?[{id:'f',filename:'evidence.txt',size:4,internal:false}]:[]});
 render(<AttachmentsPanel api={api} kind="remediation" target="r" canWrite/>);
 await screen.findByText('No attachments.');
 const file=new File(['test'],'evidence.txt',{type:'text/plain'});Object.defineProperty(file,'arrayBuffer',{value:async()=>new TextEncoder().encode('test').buffer});
 await userEvent.upload(screen.getByLabelText('Text evidence file'),file);await userEvent.click(screen.getByText('Upload evidence'));
 expect(await screen.findByRole('link')).toBeTruthy();expect(api).toHaveBeenCalledWith('/files/remediation/r','POST',{filename:'evidence.txt',content:'test',internal:false});
});
it('shows upload failure without claiming persistence',async()=>{
 const api=vi.fn(async(p:string,m?:string)=>{if(m==='POST')throw new Error('Record is closed.');return []});
 render(<AttachmentsPanel api={api} kind="support" target="t" canWrite/>);
 await screen.findByText('No attachments.');
 const file=new File(['test'],'evidence.txt',{type:'text/plain'});Object.defineProperty(file,'arrayBuffer',{value:async()=>new TextEncoder().encode('test').buffer});
 await userEvent.upload(screen.getByLabelText('Text evidence file'),file);await userEvent.click(screen.getByText('Upload evidence'));
 expect((await screen.findByRole('alert')).textContent).toContain('closed');expect(screen.queryByRole('link')).toBeNull();
});
it('sends PNG bytes with explicit binary encoding and keeps the protected download',async()=>{
 let saved=false;const api=vi.fn(async(p:string,m?:string)=>{if(m==='POST'){saved=true;return {id:'png'}}return saved?[{id:'png',filename:'screen.png',size:3,internal:false}]:[]});
 render(<AttachmentsPanel api={api} kind="support" target="t" canWrite/>);await screen.findByText('No attachments.');
 const file=new File([new Uint8Array([1,2,3])],'screen.png',{type:'image/png'});Object.defineProperty(file,'arrayBuffer',{value:async()=>new Uint8Array([1,2,3]).buffer});
 await userEvent.upload(screen.getByLabelText('Text evidence file'),file);await userEvent.click(screen.getByText('Upload evidence'));
 expect(api).toHaveBeenCalledWith('/files/support/t','POST',{filename:'screen.png',content:'AQID',encoding:'base64',internal:false});
 expect((await screen.findByRole('link')).getAttribute('href')).toBe('/api/files/support/t/png');
});
