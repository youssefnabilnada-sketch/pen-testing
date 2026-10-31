import {render,screen,fireEvent,cleanup} from '@testing-library/react';
import {afterEach,expect,it,vi} from 'vitest';
import Navigation,{GettingStarted} from '../app/console/WorkspaceNavigation';
afterEach(cleanup);
it('keeps primary actions visible and advanced tools discoverable',()=>{const go=vi.fn();render(<Navigation page="Assets" onNavigate={go}/>);expect(screen.getByRole('button',{name:'My websites'}).getAttribute('aria-current')).toBe('page');expect(screen.queryByRole('button',{name:'Launch Guard'})).toBeNull();fireEvent.click(screen.getByRole('button',{name:/Tools & settings/}));fireEvent.click(screen.getByRole('button',{name:'Launch Guard'}));expect(go).toHaveBeenCalledWith('Launch Guard');expect(screen.queryByRole('button',{name:'Administration'})).toBeNull();});
it('exposes administration only for platform administrators',()=>{render(<Navigation page="Overview" superadmin onNavigate={()=>{}}/>);fireEvent.click(screen.getByRole('button',{name:/Tools & settings/}));expect(screen.getByRole('button',{name:'Administration'})).toBeTruthy();});
it.each([[0,0,0,'Add your website','Assets'],[1,0,0,'Verify ownership','Assets'],[1,1,0,'Approve & assess','Assets'],[1,1,1,'Review your results','Findings']])('guides stored state %s/%s/%s without automatically authorizing', (assets,verified,completed,label,target)=>{const go=vi.fn();render(<GettingStarted assets={Number(assets)} verified={Number(verified)} completed={Number(completed)} onNavigate={go}/>);expect(go).not.toHaveBeenCalled();fireEvent.click(screen.getByRole('button',{name:label+' →'}));expect(go).toHaveBeenCalledWith(target);});
it('guides Arabic customers without granting assessment permission',async()=>{
 const {Experience}=await import('../app/console/Experience');const go=vi.fn();
 render(<Experience><GettingStarted assets={1} verified={1} completed={0} onNavigate={go}/></Experience>);
 fireEvent.click(screen.getByRole('button',{name:'التبديل إلى العربية'}));
 expect(screen.getByText('إثبات الملكية منفصل عن الإذن بفحص موقعك أو تعديله.')).toBeTruthy();
 fireEvent.click(screen.getByRole('button',{name:'وافق وابدأ الفحص →'}));
 expect(go).toHaveBeenCalledWith('Assets');localStorage.clear();
});
