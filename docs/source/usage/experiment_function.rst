.. _experiment_function:

-------------------
Experiment Function
-------------------

The execution of a single experiment has to be defined within a function. The function is called with the ``keyfields`` values of a database entry. The results are meant to be processed to be written into the database, i.e. as ``resultfields``. During the experiment different information can be logged into ``logtables``.

.. code-block:: 

    import os
    from py_experimenter.result_processor import ResultProcessor

    def run_experiment(keyfields: dict, result_processor: ResultProcessor, custom_fields: dict):

        # Extracting given parameters
        seed = keyfields['seed']
        path = os.path.join(custom_fields['path'], keyfields['dataset'])

        start_time = time.time()

        # Having some loop, e.g. over epochs
        while True:

            # Do some stuff here and log the result to the logtables
            result_processor.process_logs({
                'new_best_performance': {
                    'new_best_performance': min(scores)
                },
                'epochs': {
                    'runtime': time.time() - start_time,
                    'performance': np.mean(scores),
                }
            })   
            if True:
                break

        # Write first part of final results to database
        resultfields = {
            'pipeline': pipeline, 
            'train_f1': train_f1_micro,
            'train_accuracy': train_accuracy}
        result_processor.process_results(resultfields)

        # Do more some stuff here, like evaluating on test data

        # Write final results to database
        resultfields = {
            'test_f1': np.mean(scores['test_f1_micro']),
            'test_accuracy': np.mean(scores['test_accuracy'])}
        result_processor.process_results(resultfields)



"""""""""""""""""""""""""
Push Data To Resultfields
"""""""""""""""""""""""""

``Resultfields`` can be filled any time during the execution process by calling the following code within your experiment function, e.g. ``run_ml``. Note that a resultfield is meant to be written once, if you re-write a resultfield, the old value will be overwritten. Furthermore note that you do not have to write all resultfields at once, but can also only write a subset as demonstrated in the example above. Multiple in-depth examples showcasing the usage of resultfields can be found within the :ref:`examples section <examples>`.

.. code-block:: 

    result_processor.process_results({
            '<resultfield_name>': <resultfield_value>, 
            '<resultfield_name>': <resultfield_value>, 
            ...
    })


""""""""""""""""""""""
Push Data To Logtables
""""""""""""""""""""""

``Logtables`` can be filled any time during the execution process by calling the following code within your experiment function, e.g. ``run_ml``. An in-depth example showcasing the usage of logtables can be found within the :ref:`examples section <examples>`.

.. code-block:: 

    result_processor.process_logs({
        '<logtable_name>': {
            '<logtable_field_name>': <logtable_field_value>,
            '<logtable_field_name>': <logtable_field_value>,
            ...
        },
        ...
    })
