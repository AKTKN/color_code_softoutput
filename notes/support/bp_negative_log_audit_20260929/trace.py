"""Independent physical maps, GF(2) exhaustive stage minima and failure traces."""
from collections import Counter
import json
import numpy as np
import stim
from scipy.special import expit
from scipy.sparse import csc_matrix
from scipy.sparse.csgraph import connected_components
from ldpc import BpDecoder
from color_code_stim.decoders.concat_matching_decoder import ConcatMatchingDecoder
from color_code_stim.stim_utils import dem_to_parity_check
from audit import OUT,ARCHIVE,code,write

class AffineSpace:
    def __init__(self,h):
        r=np.asarray(h,dtype=np.uint8).copy()
        self.h=r.copy();m,n=r.shape;e=np.eye(m,dtype=np.uint8);piv=[];k=0
        for j in range(n):
            found=np.flatnonzero(r[k:,j])
            if not len(found):continue
            i=k+found[0];r[[i,k]]=r[[k,i]];e[[i,k]]=e[[k,i]]
            for i in np.flatnonzero(r[:,j]):
                if i!=k:r[i]^=r[k];e[i]^=e[k]
            piv.append(j);k+=1
        free=[j for j in range(n) if j not in piv]
        assert len(free)<=16,(m,n,len(free))
        bits=((np.arange(2**len(free))[:,None]>>np.arange(len(free)))&1).astype(np.uint8)
        basis=np.zeros((len(bits),n),dtype=np.uint8);basis[:,free]=bits
        basis[:,piv]=(bits@r[:k,free].T)%2
        self.e=e;self.piv=piv;self.k=k;self.basis=basis
    def solve(self,syndrome):
        rhs=(self.e@np.asarray(syndrome,dtype=np.uint8))%2
        assert not rhs[self.k:].any()
        base=np.zeros(self.h.shape[1],dtype=np.uint8);base[self.piv]=rhs[:self.k]
        solutions=self.basis^base
        assert np.all((solutions@self.h.T)%2==syndrome)
        return solutions

def exact_graph_minimum(h,p,syndrome,correction):
    h=csc_matrix(h,dtype=np.int64)
    _,labels=connected_components(h.T@h,directed=False)
    total=0.
    for label in np.unique(labels):
        ids=np.flatnonzero(labels==label);rows=np.unique(h[:,ids].nonzero()[0])
        sub=h[rows,:][:,ids].toarray().astype(np.uint8)
        sols=AffineSpace(sub).solve(np.asarray(syndrome)[rows])
        w=np.log((1-p[ids])/p[ids])
        best=float(np.min(sols@w));obtained=float(correction[ids]@w)
        assert abs(best-obtained)<1e-5,(best,obtained)
        total+=best
    assert np.array_equal((h@correction.astype(np.uint8))%2,syndrome)
    return total

if __name__=='__main__':
    z=np.load(ARCHIVE/'physical_inputs.npz');det=z['detectors'];actual=z['observables']
    data=np.load(OUT/'physical_min_sum.npz');bad=np.flatnonzero(data['prediction']!=actual)
    c=code();proj=c.dem_manager.global_projection
    # Re-inject all physical single Pauli faults into today's circuit.
    flat=c.circuit.flattened();locations=[k for k,x in enumerate(flat) if x.name=='DEPOLARIZE1']
    assert len(locations)==1;k=locations[0]
    physical=[]
    for q in flat[k].targets_copy():
        for pauli in ('X','Y','Z'):
            cc=flat[:k]+stim.Circuit(f'{pauli}_ERROR(1) {q.value}')+flat[k+1:]
            dd,oo=cc.compile_detector_sampler(seed=991).sample(2,separate_observables=True)
            assert np.all(dd==dd[0]) and np.all(oo==oo[0])
            physical.append(tuple(np.r_[dd[0],oo[0]]))
    assert np.array_equal(np.array(physical)[:,:-1],det[:57])
    global_keys=[tuple(np.r_[proj.H[:,j].toarray().ravel(),proj.observables[:,j].toarray().ravel()]) for j in range(len(proj.priors))]
    source=[global_keys.index(key) for key in physical]
    expected_groups=set()
    for ix,iy,iz in np.array(source).reshape(-1,3):
        expected_groups.update([frozenset((ix,iy)),frozenset((iz,iy))])
    assert set(map(frozenset,proj.sources))==expected_groups
    direct=BpDecoder(proj.H.astype(np.uint8),error_channel=proj.priors,max_iter=20,
                     bp_method='min_sum',schedule='parallel',input_vector_type='syndrome')
    wrapper_corr,wrapper_llr,wrapper_conv=c.decode_bp(det[bad],max_iter=20,bp_method='min_sum',schedule='parallel')
    traces=[];stage_checks=0
    for offset,i in enumerate(bad):
        direct_corr=direct.decode(det[i]).astype(np.uint8)
        assert not direct.converge and not wrapper_conv[offset]
        np.testing.assert_array_equal(direct_corr,wrapper_corr[offset])
        np.testing.assert_array_equal(direct.log_prob_ratios,wrapper_llr[offset])
        q=expit(-direct.log_prob_ratios)
        # Two physical Pauli mechanisms contribute to each CSS mechanism.
        p=np.array([q[a]*(1-q[b])+(1-q[a])*q[b] for a,b in proj.sources])
        np.testing.assert_allclose(p,proj.probabilities(q),atol=1e-15)
        effective=p/(1+p)
        independent=stim.DetectorErrorModel()
        for value,targets in zip(effective,proj.targets):
            independent.append('error',float(value),list(targets))
        independent+=proj.metadata
        manager=c.dem_manager.with_dem(independent)
        np.testing.assert_allclose(manager.probs_xz,np.clip(effective,1e-14,.5),atol=1e-15)
        implementation=c.dem_manager.with_dem(proj.project(q,negative_log_weights=True))
        np.testing.assert_allclose(manager.probs_xz,implementation.probs_xz,atol=1e-15)
        decoder=ConcatMatchingDecoder(manager,color_correlated_weight_basis='original_dem')
        pred,extra=decoder.decode(det[i:i+1],full_output=True,return_candidate_data=True,check_validity=True)
        assert pred[0]==data['prediction'][i]
        candidates=extra['candidate_original_corrections'][0,:,0,:].astype(np.uint8)
        w=np.log((1-manager.probs_xz)/manager.probs_xz)
        np.testing.assert_allclose(w,-np.log(np.maximum(p,1e-14/(1-1e-14))),atol=2e-13,rtol=1e-13)
        scores=candidates@w
        labels=np.asarray((candidates@manager.obs_matrix.T)%2).ravel()
        assert bool(labels[np.argmin(scores)])==bool(pred[0])
        for color in 'rgb':
            d=manager.dems_decomposed[color]
            first=decoder._decode_stage1(det[i:i+1],color)[0]
            h1,p1=d.Hs[0],d.probs[0];mask=h1.getnnz(axis=1)>0
            exact_graph_minimum(h1[mask,:],p1,det[i][mask],first)
            second,_=decoder._decode_stage2(det[i:i+1],first[None,:],color)
            syn=det[i].copy();keep=manager.detector_ids_by_color[color]
            syn[np.setdiff1d(np.arange(len(syn)),keep)]=False
            target=np.r_[syn,first]
            exact_graph_minimum(d.Hs[1],d.probs[1],target,second[0])
            stage_checks+=2
        # Exhaustive CSS Z-detector sector; its observable equals memory output.
        coords=manager.dem_xz.get_detector_coordinates()
        rows=np.array([r for r,a in coords.items() if a[3]==2])
        ids=np.unique(manager.H[rows,:].nonzero()[1])
        h=manager.H[rows,:][:,ids].toarray().astype(np.uint8)
        solutions=AffineSpace(h).solve(det[i][rows])
        logical=np.asarray((solutions@manager.obs_matrix[:,ids].T)%2).ravel()
        costs=solutions@w[ids]
        best=[float(np.min(costs[logical==v])) for v in (0,1)]
        actual_bit=int(actual[i])
        chosen=extra['error_preds'][0].astype(np.uint8)
        returned_cost=float(chosen[ids]@w[ids])
        traces.append(dict(index=int(i),faults=z['labels'][z['pairs'][i-57]].tolist(),actual=bool(actual[i]),
            prediction=bool(pred[0]),candidate_logicals=labels.tolist(),candidate_scores=scores.tolist(),
            correct_candidate=bool(np.any(labels==actual_bit)),
            exact_logical_costs=best,wrong_class_strictly_cheaper=bool(best[1-actual_bit]<best[actual_bit]-1e-8),
            exact_prefers_correct=bool(best[actual_bit]<best[1-actual_bit]-1e-8),
            returned_sector_cost=returned_cost,global_posteriors_above_half=int((q>.5).sum()),
            projected_probability_min=float(p.min()),projected_probability_max=float(p.max())))
    write('failure_traces.json',traces)
    summary=dict(failures=len(traces),direct_bp_checks=len(traces),physical_single_maps_checked=len(physical),
        exhaustive_stage_minima_checked=stage_checks,
        all_three_candidates_wrong=sum(not r['correct_candidate'] for r in traces),
        exact_wrong_class_strictly_cheaper=sum(r['wrong_class_strictly_cheaper'] for r in traces),
        exact_prefers_correct=sum(r['exact_prefers_correct'] for r in traces))
    write('trace_summary.json',summary);print(summary)
