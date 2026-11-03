"""Final manuscript figure presentation, traced to the 2 November 2026 source.

The fixed Figure 5 bounds preserve the originally submitted wide layout.
This module changes presentation only and independently asserts that numerical
artists and bar heights are unchanged relative to the underlying figure builder.
"""
from datetime import datetime, timezone
import numpy as np
from matplotlib.patches import Patch
from PIL import Image


def export_fixed(fig, out, stem, dpi=600):
    """Export the publication canvas without automatic cropping."""
    fig.canvas.draw()
    for ext in ['png', 'pdf', 'svg']:
        kw = {}
        if ext == 'pdf':
            kw['metadata'] = {'Creator': 'final_figure_layout.py',
                'CreationDate': datetime(2026, 11, 2, tzinfo=timezone.utc),
                'ModDate': datetime(2026, 11, 2, tzinfo=timezone.utc)}
        elif ext == 'svg':
            kw['metadata'] = {'Creator': 'final_figure_layout.py', 'Date': '2026-11-02'}
        p = out / (stem + '.' + ext)
        fig.savefig(p, dpi=dpi if ext == 'png' else None,
                    bbox_inches=None, facecolor='white', **kw)
        if ext == 'png':
            with Image.open(p) as image:
                image.convert('RGB').save(p, dpi=(dpi, dpi))


def style_wide_replication(fig, baseline, gate, rep):
    fig.set_layout_engine(None)
    # Axis-spine centres measured directly from original submission image5.png:
    # 6944x5682 at900dpi, x1382..3642 and4595..6855, y342..2446/3102..5206.
    # The measured original image is the design authority, not the later portrait script.
    fig.set_size_inches(6944/900,5682/900)
    bounds=[]
    for ax,(left,top,bottom) in zip(fig.axes,[(1382,342,2446),(4595,342,2446),(1382,3102,5206),(4595,3102,5206)]):
        box=(left/6944,(5682-bottom)/5682,2260/6944,(bottom-top)/5682);bounds.append(box);ax.set_position(box)
    a,b,c,d=fig.axes
    a.set_xlim(-10,68);b.set_xlim(0,64);c.set_xlim(-2.25,2.4)
    a.set_xlabel('Observed RMSE reduction (%)');b.set_xlabel('Interval-specific RMSE reduction (%)');c.set_xlabel('Observed contribution to MSE gain (K²)')
    a.set_ylim(1.90,-.25);c.set_ylim(2.28,-.25)
    for ax,letter in zip(fig.axes,'abcd'):
        ax.tick_params(axis='both',labelsize=7.5)
        ax.xaxis.label.set_fontsize(8.5);ax.yaxis.label.set_fontsize(8.5)
        for t in list(ax.texts):
            if t.get_text()==letter:t.set_position((-.11,1.12))
            else:t.set_fontsize(6.8)
        # The original image uses equal, wide axes and a horizontal legend.
    b.legend(handles=rep.component_legend_handles(),loc='lower right',bbox_to_anchor=(1.,1.02),ncol=3,frameon=False,borderaxespad=0,handletextpad=.3,columnspacing=.8,fontsize=6.3)
    a.set_xticks(np.arange(-10,61,10))
    b.set_xticks(np.arange(0,61,10))
    # Restore submitted neutral net-gain encoding, while retaining its new value/CI.
    net=next(t for t in c.texts if t.get_text().startswith('−0.'))
    for line in c.lines:
        if len(np.atleast_1d(line.get_ydata())) and np.all(np.asarray(line.get_ydata())==1.8):line.set_color(rep.COLORS['net'])
    for coll in c.collections:
        segs=coll.get_segments() if hasattr(coll,'get_segments') else []
        if segs and all(np.all(np.asarray(x)[:,1]==1.8) for x in segs):coll.set_color(rep.COLORS['net'])
    # Panel d restores original positions/widths and horizontal legend.
    for bars in list(d.containers):
        if hasattr(bars,'patches'):
            for patch in bars.patches:patch.remove()
    for t in list(d.texts):
        if t.get_text()!='d':t.remove()
    gg=gate.set_index('scope_label').loc[['combined','original','expansion']]
    xs=np.arange(3);width=.24
    for metric,label,color in zip(['coverage','certified_fraction','certified_sign_accuracy'],['Coverage','Sign supported','G18 sign agreement'],[rep.COLORS['core'],rep.COLORS['ring'],rep.COLORS['contrast']]):
        idx=['coverage','certified_fraction','certified_sign_accuracy'].index(metric);vals=gg[metric].to_numpy()*100
        bars=d.bar(xs+(idx-1)*width,vals,width=width*.92,color=color,edgecolor='none',zorder=2)
        for j,(bar,v) in enumerate(zip(bars,vals)):
            rr=gg.iloc[j]
            fraction=f'{int(rr.n_covered)}/{int(rr.n_transitions)}' if idx==0 else f'{int(rr.n_certified)}/{int(rr.n_transitions)}' if idx==1 else f'{int(rr.n_certified_correct)}/{int(rr.n_certified)}'
            d.text(bar.get_x()+bar.get_width()/2,v+1.2,f'{v:.1f}',ha='center',va='bottom',fontsize=6.6)
            d.text(bar.get_x()+bar.get_width()/2,max(2,min(v*.48,v-5)),fraction,ha='center',va='center',rotation=90,fontsize=6.2,color=rep.COLORS['ink'],fontweight='bold')
    d.set_xticks(xs,[f'{label}\n{role}\nn={int(gg.loc[key,"n_transitions"])}' for label,role,key in [('Combined','evaluation','combined'),('Original','diagnostic','original'),('Expansion','diagnostic','expansion')]])
    d.set_xlim(-.48744,2.48744);d.set_ylim(0,120);d.set_yticks(np.arange(0,121,20));d.tick_params(axis='x',labelsize=7.2,pad=5)
    d.set_ylabel('Evaluated transitions (%)',fontsize=8.5)
    d.legend(handles=[Patch(facecolor=x,label=l) for x,l in zip([rep.COLORS['core'],rep.COLORS['ring'],rep.COLORS['contrast']],['Coverage','Sign supported','G18 sign agreement'])],loc='lower left',bbox_to_anchor=(0.,1.02),ncol=3,frameon=False,borderaxespad=0,columnspacing=.8,handlelength=1.1,fontsize=6.)
    # Independent plotted-value identity checks: unchanged point and interval arrays.
    for ia in [0,1,2]:
        aa=fig.axes[ia];bb=baseline.axes[ia]
        assert len(aa.lines)==len(bb.lines) and len(aa.collections)==len(bb.collections)
        for u,v in zip(aa.lines,bb.lines):np.testing.assert_array_equal(u.get_xdata(),v.get_xdata());np.testing.assert_array_equal(u.get_ydata(),v.get_ydata())
        for u,v in zip(aa.collections,bb.collections):
            np.testing.assert_array_equal(u.get_offsets(),v.get_offsets())
            if hasattr(u,'get_segments'):
                for us,vs in zip(u.get_segments(),v.get_segments()):np.testing.assert_array_equal(us,vs)
    assert sorted(round(p.get_height(),12) for p in d.patches)==sorted(round(p.get_height(),12) for p in baseline.axes[3].patches)

