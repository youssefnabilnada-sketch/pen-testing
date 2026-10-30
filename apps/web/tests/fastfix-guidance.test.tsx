import React from 'react';
import {render,screen,cleanup} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {afterEach,it,expect,vi} from 'vitest';
import FastFixGuidance from '../app/console/FastFixGuidance';
afterEach(cleanup);
it('loads only after customer request and never claims a verified repair',async()=>{
 const api=vi.fn(async()=>({mode:'deterministic reviewed guidance',root_cause:'Source not inspected',recommended_action:'Review policy',platform_guidance:'Contact maintainer',approval:'Separate approval required',compatibility_risks:[],validation_required:[],backup_scope:'No backup created'}));
 render(<FastFixGuidance api={api} findingId="f"/>);expect(api).not.toHaveBeenCalled();
 await userEvent.click(screen.getByText('Choose a remediation path'));
 expect(await screen.findByText('Review policy')).toBeTruthy();
 expect(screen.getByText(/No fix has been applied or verified/)).toBeTruthy();
 await userEvent.selectOptions(screen.getByLabelText(/Your platform/),'wordpress');
 expect(api).toHaveBeenLastCalledWith('/findings/f/fastfix?platform=wordpress');
});
it('reports denied access without showing a previous plan',async()=>{
 const api=vi.fn(async()=>{throw new Error('Workspace access denied')});
 render(<FastFixGuidance api={api} findingId="f"/>);
 await userEvent.click(screen.getByText('Choose a remediation path'));
 expect(await screen.findByRole('alert')).toHaveProperty('textContent','Workspace access denied');
 expect(screen.queryByText('Download developer handoff')).toBeNull();
});
